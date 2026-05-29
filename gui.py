import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import config
from markdown_parser import MarkdownParser
from note_model import NoteManager
from search_engine import KnowledgeGraph, SearchEngine


class SmartNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"✨ {config.app_name} v{config.version}")
        self.root.geometry(f"{config.window_width}x{config.window_height}")

        self.colors = {
            'primary': '#667eea',
            'primary_dark': '#5568d3',
            'secondary': '#764ba2',
            'accent': '#f093fb',
            'bg_main': '#f7fafc',
            'bg_sidebar': '#2d3748',
            'bg_card': '#ffffff',
            'text_dark': '#2d3748',
            'text_light': '#718096',
            'text_white': '#ffffff',
            'border': '#e2e8f0',
            'success': '#48bb78',
            'warning': '#ed8936',
            'danger': '#f56565',
            'hover': '#edf2f7'
        }

        self.root.configure(bg=self.colors['bg_main'])

        self.note_manager = NoteManager(config.database_file, config.notes_dir)
        self.markdown_parser = MarkdownParser()
        self.search_engine = SearchEngine(config.index_file)
        self.knowledge_graph = KnowledgeGraph()

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
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建笔记", command=self.create_note, accelerator="Ctrl+N")
        file_menu.add_command(label="保存笔记", command=self.save_current_note, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="导入笔记", command=self.import_note)
        file_menu.add_command(label="导出笔记", command=self.export_note)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=self.editor_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.editor_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self.show_search, accelerator="Ctrl+F")
        edit_menu.add_command(label="替换", command=self.show_replace, accelerator="Ctrl+H")

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="预览模式", command=self.toggle_preview)
        view_menu.add_command(label="全屏", accelerator="F11")

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="统计信息", command=self.show_statistics)
        tools_menu.add_command(label="知识图谱", command=self.show_knowledge_graph)
        tools_menu.add_command(label="重建索引", command=self.rebuild_search_index)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

        self.root.bind('<Control-n>', lambda e: self.create_note())
        self.root.bind('<Control-s>', lambda e: self.save_current_note())
        self.root.bind('<Control-f>', lambda e: self.show_search())
        self.root.bind('<Control-z>', self.editor_undo)
        self.root.bind('<Control-y>', self.editor_redo)
        self.root.bind('<Control-h>', self.show_replace)

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
        self.is_modified = False

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

    def save_current_note(self):
        if not self.current_note:
            return

        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("警告", "笔记标题不能为空")
            return

        content = self.editor_text.get(1.0, tk.END).strip()
        category = self.note_category_var.get()
        tags_text = self.tags_entry.get().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        is_favorite = self.favorite_var.get()

        self.note_manager.update_note(
            self.current_note.id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            is_favorite=is_favorite
        )

        self.search_engine.remove_document(self.current_note.id)
        self.search_engine.add_document(self.current_note.id, self.current_note)

        self.is_modified = False
        self.load_notes_list()
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

        results = self.search_engine.search(query, self.note_manager.notes)

        if results:
            note_ids = [note_id for note_id, score in results]
            notes = [self.note_manager.get_note(nid) for nid in note_ids]
            notes = [n for n in notes if n]
            self.load_notes_list(notes)
        else:
            self.notes_listbox.delete(0, tk.END)
            self.notes_listbox.insert(tk.END, "未找到匹配的笔记")

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

    def toggle_preview(self):
        if self.preview_text.winfo_ismapped():
            self.preview_text.pack_forget()
            self.editor_text.pack(fill='both', expand=True)
        else:
            content = self.editor_text.get(1.0, tk.END)
            html = self.markdown_parser.parse_to_html(content)

            self.editor_text.pack_forget()
            self.preview_text.pack(fill='both', expand=True)

            self.preview_text.config(state='normal')
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, html)
            self.preview_text.config(state='disabled')

    def on_text_change(self, event):
        self.mark_modified()
        self.update_word_count()

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
        stats = self.knowledge_graph.get_statistics()

        msg = "🕸️ 知识图谱\n\n"
        msg += f"笔记节点: {stats['total_nodes']}\n"
        msg += f"连接数: {stats['total_edges']}\n"
        msg += f"孤立笔记: {stats['isolated_nodes']}\n"
        msg += f"社区数: {stats['communities']}\n"
        msg += f"平均连接: {stats['avg_connections']:.2f}\n"

        messagebox.showinfo("知识图谱", msg)

    def rebuild_search_index(self):
        self.search_engine.build_index(self.note_manager.notes)
        messagebox.showinfo("成功", "搜索索引已重建")

    def show_search(self):
        self.search_entry.focus()

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

    def show_replace(self, event=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("查找和替换")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['bg_card'])

        tk.Label(dialog, text="查找:", bg=self.colors['bg_card']).grid(row=0, column=0, padx=8, pady=8, sticky='e')
        find_entry = tk.Entry(dialog, width=28)
        find_entry.grid(row=0, column=1, padx=8, pady=8)
        tk.Label(dialog, text="替换为:", bg=self.colors['bg_card']).grid(row=1, column=0, padx=8, pady=8, sticky='e')
        repl_entry = tk.Entry(dialog, width=28)
        repl_entry.grid(row=1, column=1, padx=8, pady=8)

        def replace_all():
            find = find_entry.get()
            if not find:
                return
            repl = repl_entry.get()
            content = self.editor_text.get(1.0, tk.END)
            new_content, n = content.replace(find, repl), content.count(find)
            if n:
                self.editor_text.delete(1.0, tk.END)
                self.editor_text.insert(1.0, new_content.rstrip('\n'))
                self.mark_modified()
                self.update_word_count()
            messagebox.showinfo("替换", f"已替换 {n} 处", parent=dialog)

        tk.Button(dialog, text="全部替换", command=replace_all).grid(row=2, column=0, columnspan=2, pady=10)
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
            self.save_current_note()

        self.auto_save_job = self.root.after(config.auto_save_interval * 1000,
                                            self.start_auto_save)

    def on_closing(self):
        if self.is_modified:
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()

        config.save_config()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SmartNotesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
