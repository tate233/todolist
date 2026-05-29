import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import config
from markdown_parser import MarkdownParser
from note_model import NoteManager
from search_engine import KnowledgeGraph, SearchEngine

logger = logging.getLogger(__name__)


class SmartNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"✨ {config.app_name} v{config.version}")
        self.root.geometry(f"{config.window_width}x{config.window_height}")

        import theme  # noqa: PLC0415
        self.colors = theme.get_theme(getattr(config, 'theme', theme.DEFAULT_THEME))
        import i18n  # noqa: PLC0415
        i18n.set_language(getattr(config, 'language', i18n.DEFAULT_LANG))
        self._t = i18n.t

        self.root.configure(bg=self.colors['bg_main'])

        self.note_manager = NoteManager(config.database_file, config.notes_dir)
        self.markdown_parser = MarkdownParser()
        self.search_engine = SearchEngine(config.index_file)
        self.knowledge_graph = KnowledgeGraph()
        from history import VersionHistory  # noqa: PLC0415
        self.history = VersionHistory(config.history_file)
        from attachments import AttachmentManager  # noqa: PLC0415
        self.attachments = AttachmentManager(config.attachments_dir, config.attachments_index)
        from task_model import TaskManager  # noqa: PLC0415
        self.task_manager = TaskManager(config.tasks_db)

        self.current_note = None
        self.auto_save_job = None
        self.is_modified = False

        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.load_notes_list()
        self.rebuild_search_index()

        if config.auto_save:
            self.start_auto_save()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Sidebar.TFrame', background=self.colors['bg_sidebar'])
        style.configure('Main.TFrame', background=self.colors['bg_main'])
        style.configure('Card.TFrame', background=self.colors['bg_card'], relief='flat')

        style.configure('Title.TLabel',
                       font=('Microsoft YaHei UI', 14, 'bold'),
                       foreground=self.colors['text_white'],
                       background=self.colors['bg_sidebar'])

        style.configure('Category.TLabel',
                       font=config.ui_font,
                       foreground=self.colors['text_white'],
                       background=self.colors['bg_sidebar'])

        style.configure('Info.TLabel',
                       font=config.ui_font,
                       foreground=self.colors['text_light'],
                       background=self.colors['bg_card'])

        style.configure('Primary.TButton',
                       font=('Microsoft YaHei UI', 9, 'bold'),
                       foreground='white',
                       background=self.colors['primary'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark'])])

        style.configure('Success.TButton',
                       font=('Microsoft YaHei UI', 9),
                       foreground='white',
                       background=self.colors['success'],
                       borderwidth=0,
                       relief='flat')
        style.map('Success.TButton',
                 background=[('active', '#38a169')])

        style.configure('Danger.TButton',
                       font=('Microsoft YaHei UI', 9),
                       foreground='white',
                       background=self.colors['danger'],
                       borderwidth=0,
                       relief='flat')
        style.map('Danger.TButton',
                 background=[('active', '#e53e3e')])

        style.configure('TCombobox',
                       fieldbackground='white',
                       background=self.colors['primary'],
                       borderwidth=1,
                       relief='flat')

        style.configure('Treeview',
                       font=config.ui_font,
                       rowheight=30,
                       background='white',
                       fieldbackground='white',
                       borderwidth=0)
        style.configure('Treeview.Heading',
                       font=config.title_font,
                       background=self.colors['primary'],
                       foreground='white')

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.file"), menu=file_menu)
        file_menu.add_command(label="新建笔记", command=self.create_note, accelerator="Ctrl+N")
        file_menu.add_command(label="保存笔记", command=self.save_current_note, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="导入笔记", command=self.import_note)
        file_menu.add_command(label="导出笔记", command=self.export_note)
        file_menu.add_separator()
        file_menu.add_command(label="插入附件", command=self.insert_attachment)
        file_menu.add_command(label="立即备份", command=self.backup_now)
        file_menu.add_command(label="导出全部为 zip", command=self.export_all_zip)
        file_menu.add_command(label="从 zip 恢复", command=self.restore_from_zip)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.edit"), menu=edit_menu)
        edit_menu.add_command(label="撤销", command=self.editor_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.editor_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self.show_search, accelerator="Ctrl+F")
        edit_menu.add_command(label="替换", command=self.show_replace, accelerator="Ctrl+H")

        self._build_view_menu(menubar)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.tools"), menu=tools_menu)
        tools_menu.add_command(label="统计信息", command=self.show_statistics)
        tools_menu.add_command(label="知识图谱", command=self.show_knowledge_graph)
        tools_menu.add_command(label="重建索引", command=self.rebuild_search_index)
        tools_menu.add_command(label="数据体检", command=self.run_integrity_check)
        tools_menu.add_command(label="回收站", command=self.show_trash)
        tools_menu.add_separator()
        tools_menu.add_command(label="设置", command=self.show_settings)

        todo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.todo"), menu=todo_menu)
        todo_menu.add_command(label="待办列表", command=self.show_todo_view)
        todo_menu.add_command(label="任务仪表盘", command=self.show_dashboard)
        todo_menu.add_command(label="任务看板", command=self.show_kanban)
        todo_menu.add_command(label="任务日历", command=self.show_calendar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.help"), menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

        self._bind_shortcuts()

    def _build_view_menu(self, menubar):
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self._t("menu.view"), menu=view_menu)
        view_menu.add_command(label="预览模式", command=self.toggle_preview)
        view_menu.add_command(label="编辑/分栏/预览切换", command=self.cycle_view_mode)
        view_menu.add_command(label="笔记任务清单", command=self.show_note_tasks)
        view_menu.add_command(label="反向链接", command=self.show_backlinks)
        view_menu.add_command(label="历史版本", command=self.show_history)
        view_menu.add_command(label="全屏", accelerator="F11")

    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.create_note())
        self.root.bind('<Control-s>', lambda e: self.save_current_note())
        self.root.bind('<Control-f>', lambda e: self.show_search())
        self.root.bind('<Control-z>', self.editor_undo)
        self.root.bind('<Control-y>', self.editor_redo)
        self.root.bind('<Control-h>', self.show_replace)
        self.root.bind('<Control-b>', lambda e: self._md_wrap("bold"))
        self.root.bind('<Control-i>', lambda e: self._md_wrap("italic"))

    def create_widgets(self):
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill='both', expand=True)

        self.create_sidebar(main_container)
        self.create_editor_area(main_container)

        main_container.add(self.sidebar_frame, weight=0)
        main_container.add(self.editor_container, weight=1)

    def create_sidebar(self, parent):
        self.sidebar_frame = ttk.Frame(parent, style='Sidebar.TFrame', width=config.sidebar_width)

        header_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        header_frame.pack(fill='x', padx=15, pady=15)

        title_label = ttk.Label(header_frame, text="📝 我的笔记", style='Title.TLabel')
        title_label.pack(side='left')

        new_btn = tk.Button(header_frame, text="➕",
                           font=('Segoe UI Emoji', 12),
                           bg=self.colors['primary'],
                           fg='white',
                           activebackground=self.colors['primary_dark'],
                           activeforeground='white',
                           bd=0,
                           padx=10,
                           pady=5,
                           cursor='hand2',
                           command=self.create_note)
        new_btn.pack(side='right')

        search_frame = tk.Frame(self.sidebar_frame, bg=self.colors['bg_sidebar'])
        search_frame.pack(fill='x', padx=15, pady=10)

        search_container = tk.Frame(search_frame, bg='white', bd=0)
        search_container.pack(fill='x')

        search_icon = tk.Label(search_container, text="🔍",
                              font=('Segoe UI Emoji', 10),
                              bg='white', fg=self.colors['text_light'])
        search_icon.pack(side='left', padx=(8, 5))

        self.search_entry = tk.Entry(search_container,
                                    font=config.ui_font,
                                    bg='white',
                                    fg=self.colors['text_dark'],
                                    bd=0,
                                    insertbackground=self.colors['primary'])
        self.search_entry.pack(side='left', fill='x', expand=True, pady=8)
        self.search_entry.bind('<Return>', lambda e: self.search_notes())

        search_btn = tk.Button(search_container, text="搜索",
                              font=('Microsoft YaHei UI', 9),
                              bg=self.colors['primary'],
                              fg='white',
                              activebackground=self.colors['primary_dark'],
                              activeforeground='white',
                              bd=0,
                              padx=12,
                              pady=6,
                              cursor='hand2',
                              command=self.search_notes)
        search_btn.pack(side='right', padx=5)

        category_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        category_frame.pack(fill='x', padx=15, pady=10)

        ttk.Label(category_frame, text="📁 分类", style='Category.TLabel').pack(side='left')

        self.category_var = tk.StringVar(value="全部")
        self.category_combo = ttk.Combobox(category_frame,
                                          textvariable=self.category_var,
                                          width=13,
                                          state='readonly',
                                          font=config.ui_font)
        self.category_combo['values'] = ['全部', '⭐ 收藏'] + config.categories
        self.category_combo.pack(side='right')
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_by_category())

        list_frame = tk.Frame(self.sidebar_frame, bg=self.colors['bg_sidebar'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(5, 15))

        scrollbar = tk.Scrollbar(list_frame, bg=self.colors['bg_sidebar'])
        scrollbar.pack(side='right', fill='y')

        self.notes_listbox = tk.Listbox(list_frame,
                                       font=('Microsoft YaHei UI', 10),
                                       yscrollcommand=scrollbar.set,
                                       selectmode=tk.SINGLE,
                                       bg='white',
                                       fg=self.colors['text_dark'],
                                       selectbackground=self.colors['primary'],
                                       selectforeground='white',
                                       activestyle='none',
                                       bd=0,
                                       highlightthickness=0,
                                       relief='flat')
        self.notes_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.notes_listbox.yview)

        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)
        self.notes_listbox.bind('<Button-3>', self.show_note_context_menu)

    def create_editor_area(self, parent):
        self.editor_container = tk.Frame(parent, bg=self.colors['bg_main'])

        toolbar_frame = tk.Frame(self.editor_container, bg=self.colors['bg_card'], relief='flat')
        toolbar_frame.pack(fill='x', padx=20, pady=(15, 10))

        self.title_entry = tk.Entry(toolbar_frame,
                                    font=('Microsoft YaHei UI', 16, 'bold'),
                                    bg=self.colors['bg_card'],
                                    fg=self.colors['text_dark'],
                                    bd=0,
                                    insertbackground=self.colors['primary'])
        self.title_entry.pack(side='left', fill='x', expand=True, padx=(10, 15), pady=10)
        self.title_entry.bind('<KeyRelease>', lambda e: self.mark_modified())

        btn_frame = tk.Frame(toolbar_frame, bg=self.colors['bg_card'])
        btn_frame.pack(side='right', padx=10)

        save_btn = tk.Button(btn_frame, text="💾 保存",
                            font=('Microsoft YaHei UI', 9),
                            bg=self.colors['success'],
                            fg='white',
                            activebackground='#38a169',
                            activeforeground='white',
                            bd=0,
                            padx=15,
                            pady=8,
                            cursor='hand2',
                            command=self.save_current_note)
        save_btn.pack(side='left', padx=3)

        preview_btn = tk.Button(btn_frame, text="👁 预览",
                               font=('Microsoft YaHei UI', 9),
                               bg=self.colors['primary'],
                               fg='white',
                               activebackground=self.colors['primary_dark'],
                               activeforeground='white',
                               bd=0,
                               padx=15,
                               pady=8,
                               cursor='hand2',
                               command=self.toggle_preview)
        preview_btn.pack(side='left', padx=3)

        delete_btn = tk.Button(btn_frame, text="🗑 删除",
                              font=('Microsoft YaHei UI', 9),
                              bg=self.colors['danger'],
                              fg='white',
                              activebackground='#e53e3e',
                              activeforeground='white',
                              bd=0,
                              padx=15,
                              pady=8,
                              cursor='hand2',
                              command=self.delete_current_note)
        delete_btn.pack(side='left', padx=3)

        info_frame = tk.Frame(self.editor_container, bg=self.colors['bg_main'])
        info_frame.pack(fill='x', padx=20, pady=(5, 10))

        info_card = tk.Frame(info_frame, bg=self.colors['bg_card'], relief='flat')
        info_card.pack(fill='x', pady=5)

        tk.Label(info_card, text="📁",
                font=('Segoe UI Emoji', 10),
                bg=self.colors['bg_card'],
                fg=self.colors['text_light']).pack(side='left', padx=(10, 5))

        self.note_category_var = tk.StringVar()
        self.note_category_combo = ttk.Combobox(info_card,
                                               textvariable=self.note_category_var,
                                               width=12,
                                               state='readonly',
                                               font=config.ui_font)
        self.note_category_combo['values'] = config.categories
        self.note_category_combo.pack(side='left', padx=5, pady=8)
        self.note_category_combo.bind('<<ComboboxSelected>>', lambda e: self.mark_modified())

        tk.Label(info_card, text="🏷",
                font=('Segoe UI Emoji', 10),
                bg=self.colors['bg_card'],
                fg=self.colors['text_light']).pack(side='left', padx=(15, 5))

        self.tags_entry = tk.Entry(info_card,
                                  width=30,
                                  font=config.ui_font,
                                  bg=self.colors['bg_card'],
                                  fg=self.colors['text_dark'],
                                  bd=0,
                                  insertbackground=self.colors['primary'])
        self.tags_entry.pack(side='left', padx=5, pady=8)
        self.tags_entry.bind('<KeyRelease>', lambda e: self.mark_modified())

        self.favorite_var = tk.BooleanVar()
        fav_check = tk.Checkbutton(info_card,
                                  text="⭐ 收藏",
                                  variable=self.favorite_var,
                                  font=config.ui_font,
                                  bg=self.colors['bg_card'],
                                  fg=self.colors['text_dark'],
                                  activebackground=self.colors['bg_card'],
                                  activeforeground=self.colors['primary'],
                                  selectcolor=self.colors['bg_card'],
                                  bd=0,
                                  cursor='hand2',
                                  command=self.mark_modified)
        fav_check.pack(side='left', padx=15)

        self.word_count_label = tk.Label(info_card,
                                        text="📝 字数: 0",
                                        font=config.ui_font,
                                        bg=self.colors['bg_card'],
                                        fg=self.colors['text_light'])
        self.word_count_label.pack(side='right', padx=15)

        self._create_md_toolbar()

        status_bar = tk.Frame(self.editor_container, bg=self.colors['bg_card'])
        status_bar.pack(fill='x', side='bottom')
        self.status_label = tk.Label(status_bar, text="", anchor='w',
                                     font=config.ui_font,
                                     bg=self.colors['bg_card'],
                                     fg=self.colors['text_light'])
        self.status_label.pack(side='left', padx=15, pady=2)

        editor_frame = tk.Frame(self.editor_container, bg=self.colors['bg_main'])
        editor_frame.pack(fill='both', expand=True, padx=20, pady=(5, 15))

        editor_card = tk.Frame(editor_frame, bg='white', relief='flat')
        editor_card.pack(fill='both', expand=True)

        self.editor_text = scrolledtext.ScrolledText(editor_card,
                                                     font=('Consolas', 11),
                                                     wrap=tk.WORD,
                                                     undo=True,
                                                     bg='white',
                                                     fg=self.colors['text_dark'],
                                                     insertbackground=self.colors['primary'],
                                                     selectbackground=self.colors['primary'],
                                                     selectforeground='white',
                                                     bd=0,
                                                     padx=15,
                                                     pady=15,
                                                     relief='flat')
        self.editor_text.pack(fill='both', expand=True)
        self.editor_text.bind('<KeyRelease>', self.on_text_change)

        self.preview_text = scrolledtext.ScrolledText(editor_card,
                                                     font=('Microsoft YaHei UI', 11),
                                                     wrap=tk.WORD,
                                                     state='disabled',
                                                     bg='white',
                                                     fg=self.colors['text_dark'],
                                                     bd=0,
                                                     padx=15,
                                                     pady=15,
                                                     relief='flat')

    def load_notes_list(self, notes=None):
        self.notes_listbox.delete(0, tk.END)
        self.note_id_map = {}

        if notes is None:
            notes = self.note_manager.sort_notes(by="updated", reverse=True)

        for note in notes:
            display_text = f"{note.title}"
            if note.is_favorite:
                display_text = "⭐ " + display_text

            self.notes_listbox.insert(tk.END, display_text)
            self.note_id_map[self.notes_listbox.size() - 1] = note.id

    def on_note_select(self, event):
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        if self.is_modified and self.current_note:
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()

        index = selection[0]
        note_id = self.note_id_map.get(index)

        if note_id:
            self.load_note(note_id)

    def load_note(self, note_id):
        note = self.note_manager.get_note(note_id)
        if not note:
            return

        self.current_note = note
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note.title)

        self.editor_text.delete(1.0, tk.END)
        self.editor_text.insert(1.0, note.content)

        self.note_category_var.set(note.category)
        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, ', '.join(note.tags))
        self.favorite_var.set(note.is_favorite)

        self.update_word_count()
        self.highlight_editor()
        self._highlight_query_in_editor()
        self.is_modified = False

    def _highlight_query_in_editor(self):
        query = getattr(self, '_last_query', None)
        self.editor_text.tag_configure('search_hit', background='#ffe066')
        self.editor_text.tag_remove('search_hit', '1.0', tk.END)
        if not query:
            return
        import md_actions  # noqa: PLC0415
        content = self.editor_text.get('1.0', tk.END)[:-1]
        for start, end in md_actions.find_all_matches(content, query):
            self.editor_text.tag_add('search_hit', f'1.0 + {start} chars', f'1.0 + {end} chars')

    def create_note(self):
        if self.is_modified and self.current_note:
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()

        title = f"新笔记 {len(self.note_manager.notes) + 1}"
        note = self.note_manager.create_note(title)
        self.search_engine.add_document(note.id, note)

        self.load_notes_list()
        self.load_note(note.id)
        self.title_entry.focus()
        self.title_entry.select_range(0, tk.END)

    def _persist_current_note(self):
        """Persist the current note without any UI prompt. Returns True on save."""
        if not self.current_note:
            return False

        title = self.title_entry.get().strip()
        if not title:
            return False

        content = self.editor_text.get(1.0, tk.END).strip()
        category = self.note_category_var.get()
        tags_text = self.tags_entry.get().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        is_favorite = self.favorite_var.get()

        # Archive the pre-save snapshot for version history.
        self.history.record(self.current_note.id, self.current_note.title,
                            self.current_note.content)

        self.note_manager.update_note(
            self.current_note.id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            is_favorite=is_favorite
        )

        # Incremental, deferred-flush update instead of a full remove+add+rewrite.
        self.search_engine.update_document(self.current_note.id, self.current_note)
        # Resolve [[wikilinks]] to real note links on save.
        self.note_manager.sync_wikilinks(self.current_note.id)

        self.is_modified = False
        self.load_notes_list()
        return True

    def _set_status(self, text):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=text)

    def save_current_note(self):
        if not self.current_note:
            return
        if not self.title_entry.get().strip():
            messagebox.showwarning("警告", "笔记标题不能为空")
            return
        if self._persist_current_note():
            self._set_status(f"已保存 {datetime.now().strftime('%H:%M')}")
            messagebox.showinfo("成功", "笔记已保存")

    def delete_current_note(self):
        if not self.current_note:
            return

        if messagebox.askyesno("确认", "确定要删除这篇笔记吗？"):
            self.search_engine.remove_document(self.current_note.id)
            self.note_manager.delete_note(self.current_note.id)

            self.current_note = None
            self.title_entry.delete(0, tk.END)
            self.editor_text.delete(1.0, tk.END)
            self.tags_entry.delete(0, tk.END)

            self.load_notes_list()
            messagebox.showinfo("成功", "笔记已删除")

    def search_notes(self):
        query = self.search_entry.get().strip()
        if not query:
            self.load_notes_list()
            return

        self._last_query = query
        results = self.search_engine.search_fuzzy(query, self.note_manager.notes)

        if results:
            note_ids = [note_id for note_id, score in results]
            notes = [self.note_manager.get_note(nid) for nid in note_ids]
            notes = [n for n in notes if n]
            self.load_notes_list(notes)
            # show a context snippet for the top hit in the status bar
            top = notes[0]
            snippet, _spans = self.markdown_parser.make_snippet(top.content, query)
            if snippet:
                self._set_status(f"🔍 {top.title}: {snippet}")
        else:
            self.notes_listbox.delete(0, tk.END)
            self.notes_listbox.insert(tk.END, "未找到匹配的笔记")
            import pinyin_index  # noqa: PLC0415
            terms = [n.title for n in self.note_manager.get_all_notes()]
            sugg = pinyin_index.suggest(query, terms)
            if sugg:
                self._set_status("提示，您是否要找: " + ", ".join(sugg))

    def filter_by_category(self):
        category = self.category_var.get()

        if category == "全部":
            self.load_notes_list()
        elif "收藏" in category:
            notes = self.note_manager.get_favorite_notes()
            self.load_notes_list(notes)
        else:
            notes = self.note_manager.get_notes_by_category(category)
            self.load_notes_list(notes)

    def _configure_preview_tags(self):
        pt = self.preview_text
        pt.tag_configure('h1', font=('Microsoft YaHei UI', 20, 'bold'), spacing1=8, spacing3=6)
        pt.tag_configure('h2', font=('Microsoft YaHei UI', 16, 'bold'), spacing1=6, spacing3=4)
        pt.tag_configure('h3', font=('Microsoft YaHei UI', 13, 'bold'), spacing1=4, spacing3=2)
        pt.tag_configure('bold', font=('Microsoft YaHei UI', 11, 'bold'))
        pt.tag_configure('italic', font=('Microsoft YaHei UI', 11, 'italic'))
        pt.tag_configure('code', font=('Consolas', 10), background='#f1f1f4')
        pt.tag_configure('list', lmargin1=20, lmargin2=34)

    def _render_markdown_preview(self, content):
        pt = self.preview_text
        self._configure_preview_tags()
        pt.config(state='normal')
        pt.delete(1.0, tk.END)
        for block_type, segments in self.markdown_parser.render_blocks(content):
            if block_type == 'blank':
                pt.insert(tk.END, '\n')
                continue
            line_tags = ()
            if block_type.startswith('h'):
                line_tags = (block_type,)
            elif block_type == 'code_block':
                line_tags = ('code',)
            elif block_type == 'list':
                line_tags = ('list',)
                pt.insert(tk.END, '• ', line_tags)
            for seg_text, seg_style in segments:
                tags = line_tags + ((seg_style,) if seg_style else ())
                pt.insert(tk.END, seg_text, tags)
            pt.insert(tk.END, '\n')
        pt.config(state='disabled')

    def show_calendar(self):
        from datetime import date  # noqa: PLC0415

        import calendar_view  # noqa: PLC0415
        win = tk.Toplevel(self.root)
        win.title("任务日历")
        win.geometry("640x480")
        today = date.today()
        state = {"y": today.year, "m": today.month}

        grid = tk.Frame(win)
        grid.pack(fill='both', expand=True, padx=8, pady=8)

        def render():
            for c in grid.winfo_children():
                c.destroy()
            y, m = state["y"], state["m"]
            header = tk.Frame(grid)
            header.grid(row=0, column=0, columnspan=7, sticky='ew')
            tk.Button(header, text="◀", command=lambda: shift(-1)).pack(side='left')
            tk.Label(header, text=f"{y} 年 {m} 月",
                     font=('Microsoft YaHei UI', 12, 'bold')).pack(side='left', expand=True)
            tk.Button(header, text="▶", command=lambda: shift(1)).pack(side='right')
            for ci, name in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
                tk.Label(grid, text=name, fg=self.colors['text_light']).grid(row=1, column=ci)
            by_day = calendar_view.tasks_by_day(self.task_manager.get_all_tasks(), y, m)
            for ri, week in enumerate(calendar_view.month_matrix(y, m), start=2):
                for ci, day in enumerate(week):
                    if day == 0:
                        continue
                    cell = tk.Frame(grid, bd=1, relief='ridge', width=80, height=56)
                    cell.grid(row=ri, column=ci, sticky='nsew', padx=1, pady=1)
                    cell.grid_propagate(False)
                    is_today = (y, m, day) == (today.year, today.month, today.day)
                    fg = self.colors['primary'] if is_today else self.colors['text_dark']
                    tk.Label(cell, text=str(day), fg=fg).pack(anchor='nw')
                    n = len(by_day.get(day, []))
                    if n:
                        tk.Label(cell, text=f"{n} 项", fg=self.colors['warning'],
                                 cursor='hand2').pack(anchor='nw')
            for ci in range(7):
                grid.grid_columnconfigure(ci, weight=1)

        def shift(delta):
            state["y"], state["m"] = (calendar_view.prev_month(state["y"], state["m"])
                                      if delta < 0 else calendar_view.next_month(state["y"], state["m"]))
            render()

        render()

    def show_kanban(self):
        win = tk.Toplevel(self.root)
        win.title("任务看板")
        win.geometry("760x500")
        labels = {"todo": "待办", "in_progress": "进行中", "done": "已完成"}

        def render():
            for child in win.winfo_children():
                child.destroy()
            cols = self.task_manager.kanban_columns()
            for ci, (status, tasks) in enumerate(cols.items()):
                frame = tk.Frame(win, bd=1, relief='groove')
                frame.grid(row=0, column=ci, sticky='nsew', padx=4, pady=4)
                win.grid_columnconfigure(ci, weight=1)
                tk.Label(frame, text=f"{labels.get(status, status)} ({len(tasks)})",
                         font=('Microsoft YaHei UI', 11, 'bold')).pack(pady=4)
                for t in tasks:
                    card = tk.Frame(frame, bd=1, relief='ridge')
                    card.pack(fill='x', padx=4, pady=3)
                    tk.Label(card, text=t.title, anchor='w',
                             wraplength=200).pack(fill='x', padx=4)
                    sub = f"{t.priority}" + (f" · {t.due_date}" if t.due_date else "")
                    tk.Label(card, text=sub, anchor='w',
                             fg=self.colors['text_light']).pack(fill='x', padx=4)
                    btns = tk.Frame(card)
                    btns.pack(fill='x')
                    tk.Button(btns, text="◀", width=2,
                              command=lambda tid=t.id: (self.task_manager.move_status(tid, -1), render())
                              ).pack(side='left')
                    tk.Button(btns, text="▶", width=2,
                              command=lambda tid=t.id: (self.task_manager.move_status(tid, 1), render())
                              ).pack(side='left')
            win.grid_rowconfigure(0, weight=1)

        render()

    def show_dashboard(self):
        data = self.task_manager.dashboard_data()
        win = tk.Toplevel(self.root)
        win.title("任务仪表盘")
        win.geometry("520x460")

        sections = [
            ("⚠ 逾期", data["overdue"], self.colors['danger']),
            ("📅 今日到期", data["today"], self.colors['warning']),
            ("🔜 即将到期", data["upcoming"], self.colors['primary']),
        ]
        for title, tasks, color in sections:
            header = tk.Label(win, text=f"{title} ({len(tasks)})", anchor='w',
                              font=('Microsoft YaHei UI', 11, 'bold'), fg=color)
            header.pack(fill='x', padx=12, pady=(10, 2))
            if not tasks:
                tk.Label(win, text="  无", anchor='w', fg=self.colors['text_light']).pack(fill='x', padx=20)
            for t in tasks:
                due = f"  ·  {t.due_date}" if t.due_date else ""
                tk.Label(win, text=f"  • {t.title}{due}", anchor='w').pack(fill='x', padx=20)

    def show_todo_view(self):  # noqa: PLR0915 - cohesive view builder
        from task_model import STATUS_DONE, STATUS_TODO  # noqa: PLC0415
        win = tk.Toplevel(self.root)
        win.title("待办列表")
        win.geometry("680x460")

        cols = ("title", "priority", "status", "due")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c, txt in zip(cols, ("标题", "优先级", "状态", "截止")):
            tree.heading(c, text=txt)
        tree.pack(fill='both', expand=True, padx=8, pady=8)

        def refresh():
            tree.delete(*tree.get_children())
            for t in self.task_manager.get_all_tasks():
                tree.insert("", tk.END, iid=t.id,
                            values=(t.title, t.priority, t.status, t.due_date or ""))

        def add_task():
            self._task_dialog(win, on_done=refresh)

        def edit_task():
            sel = tree.selection()
            if sel:
                self._task_dialog(win, task_id=sel[0], on_done=refresh)

        def toggle_done():
            sel = tree.selection()
            if sel:
                task = self.task_manager.get_task(sel[0])
                new = STATUS_TODO if task.status == STATUS_DONE else STATUS_DONE
                self.task_manager.update_task(sel[0], status=new)
                refresh()

        def delete_task():
            sel = tree.selection()
            if sel and messagebox.askyesno("删除", "删除该任务？", parent=win):
                self.task_manager.delete_task(sel[0])
                refresh()

        bar = tk.Frame(win)
        bar.pack(fill='x', pady=(0, 8))
        tk.Button(bar, text="新建", command=add_task).pack(side='left', padx=6)
        tk.Button(bar, text="编辑", command=edit_task).pack(side='left', padx=6)
        tk.Button(bar, text="完成/取消", command=toggle_done).pack(side='left', padx=6)
        tk.Button(bar, text="删除", command=delete_task).pack(side='left', padx=6)
        refresh()

    def _task_dialog(self, parent, task_id=None, on_done=None):
        from task_model import PRIORITIES, STATUSES  # noqa: PLC0415
        task = self.task_manager.get_task(task_id) if task_id else None
        d = tk.Toplevel(parent)
        d.title("编辑任务" if task else "新建任务")
        d.transient(parent)

        tk.Label(d, text="标题:").grid(row=0, column=0, sticky='e', padx=6, pady=6)
        title_e = tk.Entry(d, width=30)
        title_e.grid(row=0, column=1, padx=6, pady=6)
        if task:
            title_e.insert(0, task.title)

        tk.Label(d, text="优先级:").grid(row=1, column=0, sticky='e', padx=6, pady=6)
        prio = ttk.Combobox(d, values=list(PRIORITIES), state='readonly')
        prio.set(task.priority if task else "medium")
        prio.grid(row=1, column=1, padx=6, pady=6, sticky='w')

        tk.Label(d, text="状态:").grid(row=2, column=0, sticky='e', padx=6, pady=6)
        status = ttk.Combobox(d, values=list(STATUSES), state='readonly')
        status.set(task.status if task else "todo")
        status.grid(row=2, column=1, padx=6, pady=6, sticky='w')

        tk.Label(d, text="截止(YYYY-MM-DD):").grid(row=3, column=0, sticky='e', padx=6, pady=6)
        due_e = tk.Entry(d, width=30)
        due_e.grid(row=3, column=1, padx=6, pady=6)
        if task and task.due_date:
            due_e.insert(0, task.due_date)

        def save():
            title = title_e.get().strip()
            if not title:
                messagebox.showwarning("提示", "标题不能为空", parent=d)
                return
            fields = dict(priority=prio.get(), status=status.get(),
                          due_date=due_e.get().strip() or None)
            if task:
                self.task_manager.update_task(task.id, title=title, **fields)
            else:
                self.task_manager.create_task(title, **fields)
            d.destroy()
            if on_done:
                on_done()

        tk.Button(d, text="保存", command=save).grid(row=4, column=0, columnspan=2, pady=10)
        title_e.focus()

    def show_backlinks(self):
        if not self.current_note:
            messagebox.showwarning("反向链接", "请先选择一篇笔记")
            return
        backlinks = self.note_manager.get_backlinks(self.current_note.id)
        win = tk.Toplevel(self.root)
        win.title(f"反向链接 - {self.current_note.title}")
        win.geometry("360x320")
        if not backlinks:
            tk.Label(win, text="没有其它笔记链接到本笔记").pack(padx=12, pady=12)
            return
        listbox = tk.Listbox(win)
        for n in backlinks:
            listbox.insert(tk.END, n.title)
        listbox.pack(fill='both', expand=True, padx=8, pady=8)
        ids = [n.id for n in backlinks]

        def open_sel(_e=None):
            sel = listbox.curselection()
            if sel:
                self.load_note(ids[sel[0]])
        listbox.bind('<Double-Button-1>', open_sel)

    def show_note_tasks(self):
        if not self.current_note:
            messagebox.showwarning("任务清单", "请先选择一篇笔记")
            return
        content = self.editor_text.get('1.0', tk.END)[:-1]
        tasks = self.markdown_parser.extract_tasks_with_lines(content)
        if not tasks:
            messagebox.showinfo("任务清单", "本笔记没有 - [ ] 任务项")
            return

        win = tk.Toplevel(self.root)
        win.title("笔记任务清单")
        win.geometry("420x420")

        def make_toggle(line_index, var):
            def toggle():
                text = self.editor_text.get('1.0', tk.END)[:-1]
                new = self.markdown_parser.set_task_state(text, line_index, var.get())
                self.editor_text.delete('1.0', tk.END)
                self.editor_text.insert('1.0', new)
                self.mark_modified()
                self.highlight_editor()
            return toggle

        for line_index, done, label in tasks:
            var = tk.BooleanVar(value=done)
            tk.Checkbutton(win, text=label, variable=var, anchor='w',
                           command=make_toggle(line_index, var)).pack(fill='x', padx=12, pady=2)

    def cycle_view_mode(self):
        import view_modes  # noqa: PLC0415
        self._view_mode = view_modes.next_mode(getattr(self, '_view_mode', view_modes.EDIT))
        self._apply_view_mode()

    def _apply_view_mode(self):
        import view_modes  # noqa: PLC0415
        mode = getattr(self, '_view_mode', view_modes.EDIT)
        editor_vis, preview_vis = view_modes.visibility(mode)
        # reset layout
        self.editor_text.pack_forget()
        self.preview_text.pack_forget()
        if editor_vis and preview_vis:
            self.editor_text.pack(side='left', fill='both', expand=True)
            self.preview_text.pack(side='right', fill='both', expand=True)
            self._render_markdown_preview(self.editor_text.get('1.0', tk.END))
        elif preview_vis:
            self.preview_text.pack(fill='both', expand=True)
            self._render_markdown_preview(self.editor_text.get('1.0', tk.END))
        else:
            self.editor_text.pack(fill='both', expand=True)
        self._set_status(f"视图: {mode}")

    @staticmethod
    def _html_preview_widget(parent):
        """Return an HTMLScrolledText if tkhtmlview is installed, else None."""
        try:
            from tkhtmlview import HTMLScrolledText  # noqa: PLC0415
        except ImportError:
            return None
        return HTMLScrolledText(parent, html="")

    def toggle_preview(self):
        content = self.editor_text.get(1.0, tk.END)
        # If an HTML preview backend is available, prefer it; otherwise fall
        # back to the Tk-tag renderer introduced earlier.
        if getattr(self, '_html_preview', 'unset') == 'unset':
            self._html_preview = self._html_preview_widget(self.editor_text.master)

        if self._html_preview is not None:
            if self._html_preview.winfo_ismapped():
                self._html_preview.pack_forget()
                self.editor_text.pack(fill='both', expand=True)
            else:
                self.editor_text.pack_forget()
                self._html_preview.pack(fill='both', expand=True)
                try:
                    html = self.markdown_parser.parse_to_styled_html(content)
                    self._html_preview.set_html(html)
                except Exception:
                    logger.exception("HTML 预览渲染失败，回退到标签渲染")
                    self._html_preview.pack_forget()
                    self.preview_text.pack(fill='both', expand=True)
                    self._render_markdown_preview(content)
            return

        if self.preview_text.winfo_ismapped():
            self.preview_text.pack_forget()
            self.editor_text.pack(fill='both', expand=True)
        else:
            self.editor_text.pack_forget()
            self.preview_text.pack(fill='both', expand=True)
            self._render_markdown_preview(content)

    def show_history(self):
        if not self.current_note:
            messagebox.showwarning("历史版本", "请先选择一篇笔记")
            return
        versions = self.history.get_versions(self.current_note.id)
        if not versions:
            messagebox.showinfo("历史版本", "暂无历史版本")
            return

        win = tk.Toplevel(self.root)
        win.title(f"历���版本 - {self.current_note.title}")
        win.geometry("700x500")

        listbox = tk.Listbox(win, height=8)
        for v in versions:
            listbox.insert(tk.END, f"{v['timestamp']}  ({len(v['content'])} 字符)")
        listbox.pack(fill='x', padx=8, pady=8)

        diff_text = scrolledtext.ScrolledText(win, font=('Consolas', 10))
        diff_text.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        def show_diff(_event=None):
            sel = listbox.curselection()
            if not sel:
                return
            current = self.editor_text.get(1.0, tk.END).strip()
            diff = self.history.diff(self.current_note.id, sel[0], current)
            diff_text.delete(1.0, tk.END)
            diff_text.insert(1.0, diff or "（与当前内容无差异）")

        def rollback():
            sel = listbox.curselection()
            if not sel:
                return
            snap = self.history.rollback(self.current_note.id, sel[0])
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(1.0, snap['content'])
            self.mark_modified()
            self.update_word_count()
            win.destroy()

        listbox.bind('<<ListboxSelect>>', show_diff)
        tk.Button(win, text="回滚到该版本", command=rollback).pack(pady=(0, 8))

    def _configure_editor_highlight_tags(self):
        e = self.editor_text
        e.tag_configure('md_heading', foreground='#5568d3', font=('Consolas', 11, 'bold'))
        e.tag_configure('md_quote', foreground='#718096')
        e.tag_configure('md_list', foreground='#48bb78')
        e.tag_configure('md_bold', font=('Consolas', 11, 'bold'))
        e.tag_configure('md_italic', font=('Consolas', 11, 'italic'))
        e.tag_configure('md_code', background='#f1f1f4')
        e.tag_configure('md_link', foreground='#3498db', underline=True)
        self._md_tags = ['md_heading', 'md_quote', 'md_list', 'md_bold',
                         'md_italic', 'md_code', 'md_link']

    def highlight_editor(self):
        if not getattr(config, 'enable_syntax_highlight', True):
            return
        if not hasattr(self, '_md_tags'):
            self._configure_editor_highlight_tags()
        e = self.editor_text
        for tag in self._md_tags:
            e.tag_remove(tag, '1.0', tk.END)
        content = e.get('1.0', tk.END)
        for lineno, line in enumerate(content.split('\n'), start=1):
            for tag, start, end in self.markdown_parser.highlight_spans(line):
                e.tag_add(tag, f'{lineno}.{start}', f'{lineno}.{end}')

    def _schedule_highlight(self):
        if getattr(self, '_hl_job', None):
            self.root.after_cancel(self._hl_job)
        self._hl_job = self.root.after(250, self.highlight_editor)

    def on_text_change(self, event):
        self.mark_modified()
        self.update_word_count()
        self._schedule_highlight()
        # live-refresh the preview when in split mode (debounced)
        if getattr(self, '_view_mode', 'edit') == 'split' and self.preview_text.winfo_ismapped():
            if getattr(self, '_split_job', None):
                self.root.after_cancel(self._split_job)
            self._split_job = self.root.after(
                300, lambda: self._render_markdown_preview(self.editor_text.get('1.0', tk.END)))

    def mark_modified(self):
        self.is_modified = True

    def update_word_count(self):
        content = self.editor_text.get(1.0, tk.END)
        word_count = self.markdown_parser.get_word_count(content)
        self.word_count_label.config(text=f"📝 字数: {word_count}")

    def show_note_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="打开", command=lambda: self.on_note_select(None))
        menu.add_command(label="删除", command=self.delete_current_note)
        menu.add_separator()
        menu.add_command(label="导出", command=self.export_note)

        menu.post(event.x_root, event.y_root)

    def import_note(self):
        filepath = filedialog.askopenfilename(
            title="导入笔记",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filepath:
            category = self.category_var.get()
            if category == "全部" or "收藏" in category:
                category = config.default_category

            note = self.note_manager.import_note(Path(filepath), category)
            if note:
                self.search_engine.add_document(note.id, note)
                self.load_notes_list()
                messagebox.showinfo("成功", "笔记导入成功")
            else:
                messagebox.showerror("错误", "笔记导入失败")

    def export_note(self):
        if not self.current_note:
            messagebox.showwarning("警告", "请先选择一篇笔记")
            return

        filepath = filedialog.asksaveasfilename(
            title="导出笔记",
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt")]
        )

        if filepath:
            format_type = 'md' if filepath.endswith('.md') else 'txt'
            if self.note_manager.export_note(self.current_note.id, Path(filepath), format_type):
                messagebox.showinfo("成功", "笔记导出成功")
            else:
                messagebox.showerror("错误", "笔记导出失败")

    def insert_attachment(self):
        if not self.current_note:
            messagebox.showwarning("插入附件", "请先选择一篇笔记")
            return
        filepath = filedialog.askopenfilename(
            title="选择要插入的文件",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.gif"), ("所有文件", "*.*")])
        if not filepath:
            return
        try:
            name = self.attachments.add_file(Path(filepath), self.current_note.id)
            rel = f"attachments/{name}"
            ext = Path(name).suffix.lower()
            snippet = f"![{Path(filepath).stem}]({rel})" if ext in (".png", ".jpg", ".jpeg", ".gif") \
                else f"[{Path(filepath).name}]({rel})"
            self.editor_text.insert(tk.INSERT, snippet)
            self.mark_modified()
        except Exception as e:
            messagebox.showerror("插入附件失败", str(e))

    def backup_now(self):
        import backup  # noqa: PLC0415
        try:
            self.search_engine.flush()
            self.note_manager.save_notes()
            dest = backup.create_backup(config.data_dir, config.backups_dir)
            messagebox.showinfo("备份", f"已创建备份:\n{dest.name}")
        except Exception as e:
            messagebox.showerror("备份失败", str(e))

    def export_all_zip(self):
        import backup  # noqa: PLC0415
        filepath = filedialog.asksaveasfilename(
            title="导出全部为 zip", defaultextension=".zip",
            filetypes=[("Zip 归档", "*.zip")])
        if not filepath:
            return
        try:
            self.search_engine.flush()
            self.note_manager.save_notes()
            backup.export_archive(config.data_dir, Path(filepath))
            messagebox.showinfo("导出", "全部数据已导出")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def restore_from_zip(self):
        import backup  # noqa: PLC0415
        filepath = filedialog.askopenfilename(
            title="从 zip 恢复", filetypes=[("Zip 归档", "*.zip")])
        if not filepath:
            return
        if not messagebox.askyesno("恢复", "恢复会覆盖当前数据，确定继续？"):
            return
        try:
            backup.restore_archive(Path(filepath), config.data_dir, overwrite=True)
            messagebox.showinfo("恢复", "恢复完成，请重启应用以加载数据")
        except Exception as e:
            messagebox.showerror("恢复失败", str(e))

    def show_statistics(self):
        stats = self.note_manager.get_statistics()
        search_stats = self.search_engine.get_statistics()

        msg = "📊 统计信息\n\n"
        msg += f"总笔记数: {stats['total_notes']}\n"
        msg += f"总字数: {stats['total_words']}\n"
        msg += f"收藏数: {stats['favorites']}\n\n"

        msg += "分类统计:\n"
        for category, count in stats['categories'].items():
            msg += f"  {category}: {count}\n"

        msg += f"\n索引词条: {search_stats['total_terms']}\n"

        messagebox.showinfo("统计信息", msg)

    def show_knowledge_graph(self):
        self.knowledge_graph.build_graph(self.note_manager.notes)
        import graph_view  # noqa: PLC0415
        if graph_view.is_available():
            try:
                self._show_graph_window(graph_view)
                return
            except Exception:
                logger.exception("图谱可视化失败，回退到文本摘要")
        # textual fallback (no matplotlib)
        stats = self.knowledge_graph.get_statistics()
        msg = "🕸️ 知识图谱\n\n"
        msg += f"笔记节点: {stats['total_nodes']}\n"
        msg += f"连接数: {stats['total_edges']}\n"
        msg += f"孤立笔记: {stats['isolated_nodes']}\n"
        msg += f"社区数: {stats['communities']}\n"
        msg += f"平均连接: {stats['avg_connections']:.2f}\n"
        messagebox.showinfo("知识图谱", msg)

    def _show_graph_window(self, graph_view):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: PLC0415
        win = tk.Toplevel(self.root)
        win.title("知识图谱")
        win.geometry("760x560")

        def open_node(note_id):
            self.load_note(note_id)

        fig = graph_view.build_figure(self.knowledge_graph, on_pick=open_node)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def rebuild_search_index(self):
        self.search_engine.build_index(self.note_manager.notes)
        messagebox.showinfo("成功", "搜索索引已重建")

    def show_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['bg_card'])
        pad = {'padx': 10, 'pady': 6}

        auto_save_var = tk.BooleanVar(value=config.auto_save)
        tk.Checkbutton(dialog, text="启用自动保存", variable=auto_save_var,
                       bg=self.colors['bg_card']).grid(row=0, column=0, columnspan=2, sticky='w', **pad)

        silent_var = tk.BooleanVar(value=config.silent_auto_save)
        tk.Checkbutton(dialog, text="静默自动保存（不弹窗）", variable=silent_var,
                       bg=self.colors['bg_card']).grid(row=1, column=0, columnspan=2, sticky='w', **pad)

        interval_lbl = tk.Label(dialog, text="自动保存间隔（秒）:", bg=self.colors['bg_card'])
        interval_lbl.grid(row=2, column=0, sticky='e', **pad)
        interval_var = tk.IntVar(value=config.auto_save_interval)
        interval_spin = tk.Spinbox(dialog, from_=5, to=600, textvariable=interval_var, width=8)
        interval_spin.grid(row=2, column=1, sticky='w', **pad)

        preview_var = tk.BooleanVar(value=config.enable_markdown_preview)
        tk.Checkbutton(dialog, text="启用 Markdown 预览", variable=preview_var,
                       bg=self.colors['bg_card']).grid(row=3, column=0, columnspan=2, sticky='w', **pad)

        highlight_var = tk.BooleanVar(value=config.enable_syntax_highlight)
        tk.Checkbutton(dialog, text="启用语法高亮", variable=highlight_var,
                       bg=self.colors['bg_card']).grid(row=4, column=0, columnspan=2, sticky='w', **pad)

        import theme  # noqa: PLC0415
        tk.Label(dialog, text="主题:", bg=self.colors['bg_card']).grid(row=5, column=0, sticky='e', **pad)
        theme_var = tk.StringVar(value=getattr(config, 'theme', theme.DEFAULT_THEME))
        ttk.Combobox(dialog, textvariable=theme_var, values=theme.available_themes(),
                     state='readonly', width=12).grid(row=5, column=1, sticky='w', **pad)

        import i18n  # noqa: PLC0415
        tk.Label(dialog, text="语言:", bg=self.colors['bg_card']).grid(row=6, column=0, sticky='e', **pad)
        lang_var = tk.StringVar(value=getattr(config, 'language', i18n.DEFAULT_LANG))
        ttk.Combobox(dialog, textvariable=lang_var, values=i18n.available_languages(),
                     state='readonly', width=12).grid(row=6, column=1, sticky='w', **pad)

        def apply_settings():
            config.auto_save = auto_save_var.get()
            config.silent_auto_save = silent_var.get()
            config.auto_save_interval = max(5, int(interval_var.get()))
            config.enable_markdown_preview = preview_var.get()
            config.enable_syntax_highlight = highlight_var.get()
            config.theme = theme_var.get()
            config.language = lang_var.get()
            config.save_config()
            # restart the auto-save timer so interval/toggle take effect now
            if self.auto_save_job:
                self.root.after_cancel(self.auto_save_job)
                self.auto_save_job = None
            if config.auto_save:
                self.start_auto_save()
            dialog.destroy()
            self._set_status("设置已保存（主题将在重启后完全生效）")

        tk.Button(dialog, text="保存", command=apply_settings).grid(row=7, column=0, columnspan=2, pady=12)

    def show_trash(self):
        trash = self.note_manager.get_trash()
        win = tk.Toplevel(self.root)
        win.title("回收站")
        win.geometry("420x360")

        listbox = tk.Listbox(win)
        for n in trash:
            listbox.insert(tk.END, f"{n.title}  (删除于 {n.deleted_at})")
        listbox.pack(fill='both', expand=True, padx=8, pady=8)
        ids = [n.id for n in trash]

        def restore():
            sel = listbox.curselection()
            if not sel:
                return
            note_id = ids[sel[0]]
            self.note_manager.restore_note(note_id)
            note = self.note_manager.get_note(note_id)
            if note:
                self.search_engine.add_document(note_id, note)
            self.load_notes_list()
            win.destroy()

        def purge():
            sel = listbox.curselection()
            if not sel:
                return
            if messagebox.askyesno("彻底删除", "彻底删除后不可恢复，确定？", parent=win):
                self.note_manager.purge_note(ids[sel[0]])
                win.destroy()

        btns = tk.Frame(win)
        btns.pack(fill='x', pady=(0, 8))
        tk.Button(btns, text="恢复", command=restore).pack(side='left', padx=8)
        tk.Button(btns, text="彻底删除", command=purge).pack(side='left')

    def run_integrity_check(self):
        import integrity  # noqa: PLC0415
        report = integrity.check(self.note_manager, self.search_engine, fix=False)
        if report.ok:
            messagebox.showinfo("数据体检", "未发现问题 ✅")
            return
        if messagebox.askyesno("数据体检", f"发现问题:\n{report}\n\n是否自动修复？"):
            fixed = integrity.check(self.note_manager, self.search_engine, fix=True)
            self.load_notes_list()
            messagebox.showinfo("数据体检", f"修复完成:\n{fixed}")

    def show_search(self):
        self.search_entry.focus()

    def _create_md_toolbar(self):
        bar = tk.Frame(self.editor_container, bg=self.colors['bg_card'])
        bar.pack(fill='x', padx=20)
        buttons = [
            ("B", lambda: self._md_wrap("bold")),
            ("I", lambda: self._md_wrap("italic")),
            ("</>", lambda: self._md_wrap("inline_code")),
            ("H1", lambda: self._md_line("h1")),
            ("H2", lambda: self._md_line("h2")),
            ("•", lambda: self._md_line("ul")),
            ("1.", lambda: self._md_line("ol")),
            ("❝", lambda: self._md_line("quote")),
            ("—", lambda: self._md_snippet("\n---\n")),
            ("🔗", lambda: self._md_snippet("[text](url)")),
        ]
        for label, cmd in buttons:
            tk.Button(bar, text=label, command=cmd, bd=0,
                      bg=self.colors['hover'], fg=self.colors['text_dark'],
                      padx=8, pady=2, cursor='hand2').pack(side='left', padx=2, pady=4)

    def _editor_offset(self, index):
        # convert a Tk text index to a flat character offset
        return len(self.editor_text.get('1.0', index))

    def _apply_md_result(self, new_text, caret_offset):
        self.editor_text.delete('1.0', tk.END)
        self.editor_text.insert('1.0', new_text.rstrip('\n'))
        self.editor_text.mark_set(tk.INSERT, f'1.0 + {caret_offset} chars')
        self.editor_text.focus_set()
        self.mark_modified()
        self.update_word_count()
        self.highlight_editor()

    def _md_wrap(self, kind, event=None):
        import md_actions  # noqa: PLC0415
        text = self.editor_text.get('1.0', tk.END)[:-1]
        try:
            start = self._editor_offset(tk.SEL_FIRST)
            end = self._editor_offset(tk.SEL_LAST)
        except tk.TclError:
            start = end = self._editor_offset(tk.INSERT)
        new, caret = md_actions.apply_wrap(text, start, end, kind)
        self._apply_md_result(new, caret)
        return "break"

    def _md_line(self, kind):
        import md_actions  # noqa: PLC0415
        text = self.editor_text.get('1.0', tk.END)[:-1]
        start = self._editor_offset(tk.INSERT)
        new, caret = md_actions.apply_line_prefix(text, start, kind)
        self._apply_md_result(new, caret)

    def _md_snippet(self, snippet):
        import md_actions  # noqa: PLC0415
        text = self.editor_text.get('1.0', tk.END)[:-1]
        pos = self._editor_offset(tk.INSERT)
        new, caret = md_actions.insert_snippet(text, pos, snippet)
        self._apply_md_result(new, caret)

    def editor_undo(self, event=None):
        try:
            self.editor_text.edit_undo()
        except tk.TclError:
            pass  # nothing to undo
        return "break"

    def editor_redo(self, event=None):
        try:
            self.editor_text.edit_redo()
        except tk.TclError:
            pass  # nothing to redo
        return "break"

    def show_replace(self, event=None):  # noqa: PLR0915 - cohesive dialog builder
        import md_actions  # noqa: PLC0415
        dialog = tk.Toplevel(self.root)
        dialog.title("查找和替换")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['bg_card'])

        find_lbl = tk.Label(dialog, text="查找:", bg=self.colors['bg_card'])
        find_lbl.grid(row=0, column=0, padx=8, pady=8, sticky='e')
        find_entry = tk.Entry(dialog, width=28)
        find_entry.grid(row=0, column=1, columnspan=3, padx=8, pady=8, sticky='w')
        repl_lbl = tk.Label(dialog, text="替换为:", bg=self.colors['bg_card'])
        repl_lbl.grid(row=1, column=0, padx=8, pady=8, sticky='e')
        repl_entry = tk.Entry(dialog, width=28)
        repl_entry.grid(row=1, column=1, columnspan=3, padx=8, pady=8, sticky='w')

        case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="区分大小写", variable=case_var,
                       bg=self.colors['bg_card']).grid(row=2, column=0, columnspan=2, sticky='w', padx=8)

        self.editor_text.tag_configure('find_hit', background='#ffe066')
        state = {'matches': [], 'idx': -1}

        def do_find():
            self.editor_text.tag_remove('find_hit', '1.0', tk.END)
            text = self.editor_text.get('1.0', tk.END)[:-1]
            state['matches'] = md_actions.find_all_matches(text, find_entry.get(), case_var.get())
            for start, end in state['matches']:
                self.editor_text.tag_add('find_hit', f'1.0 + {start} chars', f'1.0 + {end} chars')
            state['idx'] = -1
            count_lbl.config(text=f"{len(state['matches'])} 处匹配")
            if state['matches']:
                goto(0)

        def goto(i):
            if not state['matches']:
                return
            state['idx'] = i % len(state['matches'])
            start, _end = state['matches'][state['idx']]
            self.editor_text.see(f'1.0 + {start} chars')
            self.editor_text.mark_set(tk.INSERT, f'1.0 + {start} chars')

        def replace_all():
            text = self.editor_text.get('1.0', tk.END)[:-1]
            new, n = md_actions.replace_all(text, find_entry.get(), repl_entry.get(), case_var.get())
            if n:
                self.editor_text.delete('1.0', tk.END)
                self.editor_text.insert('1.0', new)
                self.mark_modified()
                self.update_word_count()
                self.highlight_editor()
            messagebox.showinfo("替换", f"已替换 {n} 处", parent=dialog)

        tk.Button(dialog, text="查找", command=do_find).grid(row=3, column=0, pady=8)
        tk.Button(dialog, text="上一个", command=lambda: goto(state['idx'] - 1)).grid(row=3, column=1, pady=8)
        tk.Button(dialog, text="下一个", command=lambda: goto(state['idx'] + 1)).grid(row=3, column=2, pady=8)
        tk.Button(dialog, text="全部替换", command=replace_all).grid(row=3, column=3, pady=8)
        count_lbl = tk.Label(dialog, text="", bg=self.colors['bg_card'])
        count_lbl.grid(row=4, column=0, columnspan=4)

        def on_close():
            self.editor_text.tag_remove('find_hit', '1.0', tk.END)
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        find_entry.focus()

    def show_help(self):
        help_text = """
智能笔记管理系统 - 使用说明

快捷键:
  Ctrl+N - 新建笔记
  Ctrl+S - 保存笔记
  Ctrl+F - 搜索笔记

功能说明:
1. Markdown编辑 - 支持完整的Markdown语法
2. 分类管理 - 按分类组织笔记
3. 标签系统 - 使用标签关联笔记
4. 全文搜索 - 快速查找笔记内容
5. 知识图谱 - 可视化笔记关联
6. 导入导出 - 支持Markdown和文本格式
        """
        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        about_text = f"""
{config.app_name}
版本: {config.version}
作者: {config.author}

一个功能强大的智能笔记管理系统
支持Markdown编辑、全文搜索、知识图谱等功能
        """
        messagebox.showinfo("关于", about_text)

    def start_auto_save(self):
        if config.auto_save and self.current_note and self.is_modified:
            if self._persist_current_note():
                self._set_status(f"已自动保存 {datetime.now().strftime('%H:%M')}")

        self.auto_save_job = self.root.after(config.auto_save_interval * 1000,
                                            self.start_auto_save)

    def on_closing(self):
        if self.is_modified:
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()

        self.search_engine.flush()
        config.save_config()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SmartNotesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
