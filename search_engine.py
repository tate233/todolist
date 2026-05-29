import logging
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from storage.atomic_io import atomic_write_json


logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(self, index_file: Path):
        self.index_file = index_file
        self.inverted_index = {}
        self.document_freq = {}
        self.total_docs = 0
        self.load_index()

    def load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.inverted_index = data.get('inverted_index', {})
                    self.document_freq = data.get('document_freq', {})
                    # doc_ids tracks which note ids are indexed so counting stays
                    # idempotent across edits; derive it for legacy index files.
                    saved_ids = data.get('doc_ids')
                    if saved_ids is None:
                        saved_ids = {nid for postings in self.inverted_index.values()
                                     for nid in postings}
                    self.doc_ids = set(saved_ids)
                    self.total_docs = data.get('total_docs', len(self.doc_ids))
            except Exception as e:
                logger.exception("加载索引失败: %s", e)
                self._initialize_index()
        else:
            self._initialize_index()

    def _initialize_index(self):
        self.inverted_index = {}
        self.document_freq = {}
        self.doc_ids = set()
        self.total_docs = 0

    def save_index(self):
        try:
            data = {
                'inverted_index': self.inverted_index,
                'document_freq': self.document_freq,
                'doc_ids': sorted(self.doc_ids),
                'total_docs': self.total_docs
            }
            atomic_write_json(self.index_file, data)
            return True
        except Exception as e:
            logger.exception("保存索引失败: %s", e)
            return False

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens: List[str] = []
        # Latin/number runs stay whole; CJK runs are split per-character with
        # bigram fallback so single-character queries and sub-phrases match.
        for run in re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]+', text):
            if run[0].isascii():
                tokens.append(run)
            else:
                chars = list(run)
                tokens.extend(chars)
                tokens.extend(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
        return tokens

    def build_index(self, notes: Dict):
        self._initialize_index()
        self.doc_ids = set(notes.keys())
        self.total_docs = len(self.doc_ids)

        for note_id, note in notes.items():
            text = f"{note.title} {note.content} {' '.join(note.tags)}"
            tokens = self.tokenize(text)

            term_freq = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1

            for term, freq in term_freq.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                    self.document_freq[term] = 0

                self.inverted_index[term][note_id] = freq
                self.document_freq[term] += 1

        self.save_index()

    def add_document(self, note_id: str, note):
        text = f"{note.title} {note.content} {' '.join(note.tags)}"
        tokens = self.tokenize(text)

        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1

        for term, freq in term_freq.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
                self.document_freq[term] = 0

            if note_id not in self.inverted_index[term]:
                self.document_freq[term] += 1

            self.inverted_index[term][note_id] = freq

        # Only count a genuinely new document; re-adding an existing note
        # (e.g. the save path's remove+add, or a repeated add) is a no-op.
        if note_id not in self.doc_ids:
            self.doc_ids.add(note_id)
            self.total_docs += 1
        self.save_index()

    def remove_document(self, note_id: str):
        for term in list(self.inverted_index.keys()):
            if note_id in self.inverted_index[term]:
                del self.inverted_index[term][note_id]
                self.document_freq[term] -= 1

                if self.document_freq[term] == 0:
                    del self.inverted_index[term]
                    del self.document_freq[term]

        if note_id in self.doc_ids:
            self.doc_ids.discard(note_id)
            self.total_docs = max(0, self.total_docs - 1)
        self.save_index()

    def calculate_tf_idf(self, term: str, note_id: str) -> float:
        if term not in self.inverted_index:
            return 0.0

        if note_id not in self.inverted_index[term]:
            return 0.0

        tf = self.inverted_index[term][note_id]
        df = self.document_freq[term]

        if df == 0 or self.total_docs == 0:
            return 0.0

        idf = math.log((self.total_docs + 1) / (df + 1))
        return tf * idf

    def search(self, query: str, notes: Dict, limit: int = 20) -> List[Tuple[str, float]]:
        if not query or not notes:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = defaultdict(float)

        for token in tokens:
            if token in self.inverted_index:
                for note_id in self.inverted_index[token]:
                    if note_id in notes:
                        scores[note_id] += self.calculate_tf_idf(token, note_id)

        query_lower = query.lower()
        for note_id, note in notes.items():
            if note is None:
                continue

            if query_lower in note.title.lower():
                scores[note_id] += 10.0

            if query_lower in note.content.lower():
                scores[note_id] += 5.0

            for tag in note.tags:
                if query_lower in tag.lower():
                    scores[note_id] += 8.0

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]

    def get_related_notes(self, note_id: str, notes: Dict, limit: int = 5) -> List[Tuple[str, float]]:
        if note_id not in notes:
            return []

        note = notes[note_id]
        text = f"{note.title} {note.content} {' '.join(note.tags)}"
        tokens = self.tokenize(text)

        scores = defaultdict(float)

        for token in tokens:
            if token in self.inverted_index:
                for other_id in self.inverted_index[token]:
                    if other_id != note_id and other_id in notes:
                        scores[other_id] += self.calculate_tf_idf(token, other_id)

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]

    def get_popular_terms(self, limit: int = 20) -> List[Tuple[str, int]]:
        term_scores = []

        for term, df in self.document_freq.items():
            if len(term) > 2:
                term_scores.append((term, df))

        sorted_terms = sorted(term_scores, key=lambda x: x[1], reverse=True)
        return sorted_terms[:limit]

    def suggest_query(self, partial_query: str, limit: int = 5) -> List[str]:
        if not partial_query:
            return []

        partial_lower = partial_query.lower()
        suggestions = [term for term in self.inverted_index.keys() if term.startswith(partial_lower)]

        suggestions.sort(key=lambda x: self.document_freq.get(x, 0), reverse=True)
        return suggestions[:limit]

    def get_statistics(self) -> Dict:
        return {
            'total_documents': self.total_docs,
            'total_terms': len(self.inverted_index),
            'avg_terms_per_doc': len(self.inverted_index) / max(1, self.total_docs),
            'index_size': len(str(self.inverted_index))
        }

class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def build_graph(self, notes: Dict):
        self.nodes = {}
        self.edges = []

        for note_id, note in notes.items():
            self.nodes[note_id] = {
                'id': note_id,
                'title': note.title,
                'category': note.category,
                'tags': note.tags,
                'links': note.links
            }

        for note_id, note in notes.items():
            for linked_id in note.links:
                if linked_id in self.nodes:
                    self.edges.append((note_id, linked_id))

        for note_id, note in notes.items():
            for other_id, other_note in notes.items():
                if note_id != other_id:
                    common_tags = set(note.tags) & set(other_note.tags)
                    if len(common_tags) >= 2:
                        edge = (note_id, other_id)
                        if edge not in self.edges and (other_id, note_id) not in self.edges:
                            self.edges.append(edge)

    def get_connected_notes(self, note_id: str, depth: int = 1) -> List[str]:
        if note_id not in self.nodes:
            return []

        adjacency = self._build_adjacency()
        connected = set()
        current_level = {note_id}

        for _ in range(depth):
            next_level = set()
            for node in current_level:
                for neighbor in adjacency.get(node, ()):
                    if neighbor not in connected:
                        next_level.add(neighbor)

            connected.update(next_level)
            current_level = next_level

        connected.discard(note_id)
        return list(connected)

    def get_central_notes(self, limit: int = 10) -> List[Tuple[str, int]]:
        degree = defaultdict(int)

        for edge in self.edges:
            degree[edge[0]] += 1
            degree[edge[1]] += 1

        sorted_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:limit]

    def get_isolated_notes(self) -> List[str]:
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge[0])
            connected_nodes.add(edge[1])

        isolated = [node_id for node_id in self.nodes if node_id not in connected_nodes]

        return isolated

    def _build_adjacency(self) -> Dict[str, set]:
        """Build an undirected adjacency map once, instead of rescanning the
        full edge list for every node visit."""
        adjacency = {node_id: set() for node_id in self.nodes}
        for a, b in self.edges:
            if a in adjacency:
                adjacency[a].add(b)
            if b in adjacency:
                adjacency[b].add(a)
        return adjacency

    def get_communities(self) -> List[List[str]]:
        adjacency = self._build_adjacency()
        visited = set()
        communities = []

        # Iterative connected-components (explicit stack) avoids the recursion
        # depth limit / stack overflow the previous recursive DFS hit on long
        # note chains.
        for start in self.nodes:
            if start in visited:
                continue
            stack = [start]
            community = []
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                community.append(node)
                for neighbor in adjacency.get(node, ()):
                    if neighbor not in visited:
                        stack.append(neighbor)
            if len(community) > 1:
                communities.append(community)

        return communities

    def get_shortest_path(self, start_id: str, end_id: str) -> List[str]:
        if start_id not in self.nodes or end_id not in self.nodes:
            return []

        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current, path = queue.pop(0)

            if current == end_id:
                return path

            for edge in self.edges:
                next_node = None
                if edge[0] == current and edge[1] not in visited:
                    next_node = edge[1]
                elif edge[1] == current and edge[0] not in visited:
                    next_node = edge[0]

                if next_node:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return []

    def get_statistics(self) -> Dict:
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'isolated_nodes': len(self.get_isolated_notes()),
            'communities': len(self.get_communities()),
            'avg_connections': len(self.edges) * 2 / max(1, len(self.nodes))
        }
