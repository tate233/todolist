# Last modified at 2026/05/24 星期日 15:04:02
import logging
import re
from typing import Dict, List, Tuple

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    """Count words in Markdown text, ignoring code spans/blocks and markup.

    Single source of truth for word counting so the note model, the editor
    word-count label and the statistics panel all report the same number.
    """
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'[#\*\-\[\]\(\)_]', '', text)
    return len(text.split())


class MarkdownParser:
    def __init__(self):
        self.md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'tables',
            'fenced_code',
            'toc'
        ])

        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*|__(.+?)__')
        self.italic_pattern = re.compile(r'\*(.+?)\*|_(.+?)_')
        self.list_pattern = re.compile(r'^[\*\-\+]\s+(.+)$', re.MULTILINE)
        self.task_pattern = re.compile(r'^\s*[-*]\s+\[([ x])\]\s+(.+)$', re.MULTILINE)

    def parse_to_html(self, text: str) -> str:
        try:
            html = self.md.convert(text)
            self.md.reset()
            return html
        except Exception as e:
            logger.exception("Markdown解析失败: %s", e)
            return f"<pre>{text}</pre>"

    def extract_headings(self, text: str) -> List[Tuple[int, str]]:
        headings = []
        for match in self.heading_pattern.finditer(text):
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title))
        return headings

    def extract_links(self, text: str) -> List[Tuple[str, str]]:
        links = []
        for match in self.link_pattern.finditer(text):
            link_text = match.group(1)
            link_url = match.group(2)
            links.append((link_text, link_url))
        return links

    def extract_images(self, text: str) -> List[Tuple[str, str]]:
        images = []
        for match in self.image_pattern.finditer(text):
            alt_text = match.group(1)
            image_url = match.group(2)
            images.append((alt_text, image_url))
        return images

    def extract_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        code_blocks = []
        for match in self.code_block_pattern.finditer(text):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            code_blocks.append((language, code))
        return code_blocks

    def extract_tasks(self, text: str) -> List[Tuple[bool, str]]:
        tasks = []
        for match in self.task_pattern.finditer(text):
            is_completed = match.group(1).lower() == 'x'
            task_text = match.group(2).strip()
            tasks.append((is_completed, task_text))
        return tasks

    def get_word_count(self, text: str) -> int:
        return count_words(text)

    _inline_re = re.compile(r'(\*\*.+?\*\*|__.+?__|\*[^*]+?\*|_[^_]+?_|`[^`]+`)')

    def render_inline(self, line: str) -> List[Tuple[str, str]]:
        """Split a line into (text, style) segments for Tk Text rendering.

        style is one of: '', 'bold', 'italic', 'code'.
        """
        segments: List[Tuple[str, str]] = []
        pos = 0
        for m in self._inline_re.finditer(line):
            if m.start() > pos:
                segments.append((line[pos:m.start()], ''))
            tok = m.group(0)
            if tok.startswith('**') or tok.startswith('__'):
                segments.append((tok[2:-2], 'bold'))
            elif tok.startswith('`'):
                segments.append((tok[1:-1], 'code'))
            else:
                segments.append((tok[1:-1], 'italic'))
            pos = m.end()
        if pos < len(line):
            segments.append((line[pos:], ''))
        return segments or [(line, '')]

    def render_blocks(self, text: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """Lightweight structural parse for the Tk preview.

        Returns a list of (block_type, inline_segments) where block_type is
        one of: h1/h2/h3, list, code_block, blank, para.
        """
        blocks: List[Tuple[str, List[Tuple[str, str]]]] = []
        in_code = False
        for raw in text.split('\n'):
            if raw.strip().startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                blocks.append(('code_block', [(raw, 'code')]))
                continue
            heading = self.heading_pattern.match(raw)
            if heading:
                level = min(len(heading.group(1)), 3)
                blocks.append((f'h{level}', [(heading.group(2).strip(), '')]))
            elif re.match(r'^\s*[-*+]\s+', raw):
                item = re.sub(r'^\s*[-*+]\s+(\[[ xX]\]\s+)?', '', raw)
                blocks.append(('list', self.render_inline(item)))
            elif raw.strip() == '':
                blocks.append(('blank', [('', '')]))
            else:
                blocks.append(('para', self.render_inline(raw)))
        return blocks

    def get_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        word_count = self.get_word_count(text)
        minutes = max(1, round(word_count / words_per_minute))
        return minutes

    def highlight_code(self, code: str, language: str = 'python') -> str:
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
            except Exception:
                lexer = get_lexer_by_name('text')

        formatter = HtmlFormatter(style='monokai', noclasses=True)
        return highlight(code, lexer, formatter)

    def create_toc(self, text: str) -> str:
        headings = self.extract_headings(text)
        if not headings:
            return ""

        toc = "## 目录\n\n"
        for level, title in headings:
            indent = "  " * (level - 1)
            anchor = title.lower().replace(' ', '-')
            toc += f"{indent}- [{title}](#{anchor})\n"

        return toc

    def add_syntax_highlighting(self, text: str) -> str:
        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            highlighted = self.highlight_code(code, language)
            return f'<div class="code-block">{highlighted}</div>'

        return self.code_block_pattern.sub(replace_code_block, text)

    def extract_metadata(self, text: str) -> Dict:
        lines = text.split('\n')
        metadata = {}

        if lines and lines[0].strip() == '---':
            i = 1
            while i < len(lines) and lines[i].strip() != '---':
                line = lines[i].strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                i += 1

        return metadata

    def format_markdown(self, text: str) -> str:
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False

        for line in lines:
            t = line.strip()
            if t.startswith('```'):
                in_code_block = not in_code_block
                t = line
            elif in_code_block:
                t = line
            else:
                t = line.rstrip()
            formatted_lines.append(t)

        return '\n'.join(formatted_lines)

    def convert_to_plain_text(self, text: str) -> str:
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'[#\*\-_]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def search_in_markdown(self, text: str, keyword: str) -> List[Tuple[int, str]]:
        if not keyword:
            return []

        keyword = keyword.lower()
        results = []
        lines = text.split('\n')

        for i, line in enumerate(lines, 1):
            if keyword in line.lower():
                results.append((i, line.strip()))

        return results

    def get_statistics(self, text: str) -> Dict:
        return {
            'word_count': self.get_word_count(text),
            'char_count': len(text),
            'line_count': len(text.split('\n')),
            'heading_count': len(self.extract_headings(text)),
            'link_count': len(self.extract_links(text)),
            'image_count': len(self.extract_images(text)),
            'code_block_count': len(self.extract_code_blocks(text)),
            'task_count': len(self.extract_tasks(text)),
            'reading_time': self.get_reading_time(text)
        }
