import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import easyocr
from pathlib import Path
import os
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import cv2
import numpy as np

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Text Extractor")
        self.root.geometry("1400x900")
        self.root.configure(bg="#ffffff")
        
        # Appleスタイルのカラーパレット
        self.colors = {
            'bg': '#ffffff',
            'secondary_bg': '#f5f5f7',
            'tertiary_bg': '#e8e8ed',
            'text': '#1d1d1f',
            'secondary_text': '#86868b',
            'accent': '#0071e3',
            'accent_hover': '#0077ed',
            'success': '#34c759',
            'warning': '#ff9500',
            'error': '#ff3b30',
            'border': '#e5e5ea',
            'shadow': '#00000010'
        }
        
        self.extracted_text = ""
        self.current_image_path = ""
        self.reader = None
        self.photo_image = None
        self.font_size_var = None
        self.is_processing = False
        
        self.setup_ui()
        self.init_reader()
        
    def init_reader(self):
        """OCRリーダーを初期化"""
        try:
            self.update_status("OCR エンジンを初期化中...", self.colors['warning'])
            self.root.update()
            self.reader = easyocr.Reader(['ja', 'en'])
            self.update_status("準備完了", self.colors['success'])
        except Exception as e:
            messagebox.showerror("エラー", f"OCR エンジンの初期化に失敗しました:\n{str(e)}")
            self.update_status("エラー", self.colors['error'])
        
    def setup_ui(self):
        """UIを構築"""
        # メインコンテナ
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダー
        self._create_header(main_container)
        
        # コンテンツ領域（左右2カラムレイアウト）
        content_container = tk.Frame(main_container, bg=self.colors['bg'])
        content_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # 左側：サムネイル
        self._create_left_panel(content_container)
        
        # 右側：ドラッグエリア、ボタン、テキスト表示
        self._create_right_panel(content_container)
        
        # ステータスバー
        self._create_status_bar(main_container)
    
    def _create_header(self, parent):
        """ヘッダーを作成"""
        header_frame = tk.Frame(parent, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        
        title = tk.Label(
            header_frame,
            text="imageOCR",
            font=("SF Pro Display", 18, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title.pack(anchor="w")
        
        subtitle = tk.Label(
            header_frame,
            text="高精度なOCRで画像からテキストを抽出します",
            font=("SF Pro Text", 8),
            bg=self.colors['bg'],
            fg=self.colors['secondary_text']
        )
        subtitle.pack(anchor="w", pady=(5, 0))
    
    def _create_left_panel(self, parent):
        """左パネル（サムネイル）を作成"""
        left_frame = tk.Frame(parent, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 20))
        
        # サムネイル背景
        thumbnail_bg = tk.Frame(
            left_frame,
            bg=self.colors['secondary_bg'],
            relief=tk.FLAT,
            bd=0,
            width=300,
            height=550
        )
        thumbnail_bg.pack_propagate(False)
        thumbnail_bg.pack()
        
        # サムネイル表示
        self.thumbnail_widget = tk.Label(
            thumbnail_bg,
            bg=self.colors['secondary_bg'],
            fg=self.colors['secondary_text'],
            font=("SF Pro Text", 11),
            text="画像を選択してください",
            relief=tk.FLAT,
            bd=0
        )
        self.thumbnail_widget.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    def _create_right_panel(self, parent):
        """右パネル（ドラッグエリア、ボタン、テキスト表示）を作成"""
        right_frame = tk.Frame(parent, bg=self.colors['bg'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 上部ボタンフレーム
        self._create_button_frame(right_frame)
        
        # ドラッグアンドドロップエリア
        self._create_drop_area(right_frame)
        
        # テキスト表示ラベル
        text_label = tk.Label(
            right_frame,
            text="抽出されたテキスト",
            font=("SF Pro Text", 13, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            anchor="w"
        )
        text_label.pack(fill=tk.X, pady=(15, 8))
        
        # フォントサイズコントロール
        self._create_font_control(right_frame)
        
        # テキストエリア
        self._create_text_area(right_frame)
    
    def _create_drop_area(self, parent):
        """ドラッグアンドドロップエリアを作成"""
        drop_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT, bd=0, height=100)
        drop_frame.pack(pady=10, fill=tk.X, ipady=25)
        drop_frame.pack_propagate(False)
        
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        icon = tk.Label(
            drop_frame,
            text="🖼️",
            font=("Arial", 32),
            bg=self.colors['secondary_bg'],
            fg=self.colors['accent']
        )
        icon.pack()
        
        text1 = tk.Label(
            drop_frame,
            text="ここに画像をドラッグ",
            font=("SF Pro Text", 12, "bold"),
            bg=self.colors['secondary_bg'],
            fg=self.colors['text'],
            cursor="hand2"
        )
        text1.pack()
        
        text2 = tk.Label(
            drop_frame,
            text="またはクリックして選択",
            font=("SF Pro Text", 11),
            bg=self.colors['secondary_bg'],
            fg=self.colors['secondary_text'],
            cursor="hand2"
        )
        text2.pack()
        
        for widget in [drop_frame, icon, text1, text2]:
            widget.bind("<Button-1>", lambda e: self.select_file())
    
    def _create_button_frame(self, parent):
        """ボタンフレームを作成"""
        btn_frame = tk.Frame(parent, bg=self.colors['bg'])
        btn_frame.pack(pady=(0, 15), fill=tk.X, padx=0)
        
        select_btn = self._create_button(
            btn_frame,
            "ファイル選択",
            self.select_file,
            self.colors['accent']
        )
        select_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = self._create_button(
            btn_frame,
            "クリア",
            self.clear_text,
            self.colors['error']
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_button(self, parent, text, command, color):
        """スタイル付きボタンを作成"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            font=("SF Pro Text", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            bd=0,
            activebackground=color,
            activeforeground="white",
            cursor="hand2"
        )
        btn.config(highlightthickness=0)
        return btn
    
    def _create_text_area(self, parent):
        """テキスト入力エリアを作成"""
        text_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT, bd=0)
        text_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame, bg=self.colors['secondary_bg'], troughcolor=self.colors['secondary_bg'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_widget = tk.Text(
            text_frame,
            font=("SF Mono", 11),
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            bg=self.colors['secondary_bg'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=12,
            insertbackground=self.colors['accent']
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
    
    def _create_font_control(self, parent):
        """フォントサイズコントロールを作成"""
        font_frame = tk.Frame(parent, bg=self.colors['bg'])
        font_frame.pack(pady=12, fill=tk.X, padx=0)
        
        font_label = tk.Label(
            font_frame,
            text="フォント サイズ",
            font=("SF Pro Text", 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        font_label.pack(side=tk.LEFT, padx=0)
        
        self.font_size_var = tk.IntVar(value=11)
        
        font_scale = tk.Scale(
            font_frame,
            from_=9,
            to=98,
            orient=tk.HORIZONTAL,
            variable=self.font_size_var,
            command=self.change_font_size,
            bg=self.colors['tertiary_bg'],
            fg=self.colors['accent'],
            troughcolor=self.colors['secondary_bg'],
            relief=tk.FLAT,
            bd=0,
            length=200,
            highlightthickness=0
        )
        font_scale.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)
        
        self.size_display = tk.Label(
            font_frame,
            text="11",
            font=("SF Pro Text", 10, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            width=2
        )
        self.size_display.pack(side=tk.LEFT, padx=15)
    def _create_status_bar(self, parent):
        """ステータスバーを作成"""
        status_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            status_frame,
            text="準備完了",
            font=("SF Pro Text", 10),
            bg=self.colors['secondary_bg'],
            fg=self.colors['secondary_text'],
            anchor="w",
            padx=20,
            pady=10
        )
        self.status_label.pack(fill=tk.X)
    
    def update_status(self, text, color):
        """ステータスを更新"""
        self.status_label.config(text=text, fg=color)
        self.root.update()
    
    def on_drop(self, event):
        """ドラッグアンドドロップ処理"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0].strip('{}')
            self.process_image(file_path)
    
    def select_file(self):
        """ファイル選択ダイアログ"""
        file_path = filedialog.askopenfilename(
            title="画像ファイルを選択",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            self.process_image(file_path)
    
    def display_thumbnail(self, image_path):
        """サムネイルを表示"""
        try:
            img = Image.open(image_path)
            img.thumbnail((280, 520), Image.Resampling.LANCZOS)
            
            self.photo_image = ImageTk.PhotoImage(img)
            self.thumbnail_widget.config(image=self.photo_image, text="")
        except Exception as e:
            print(f"サムネイル表示エラー: {e}")
            self.thumbnail_widget.config(text="画像表示\n失敗", image="")
    
    def process_image(self, file_path):
        """画像を別スレッドで処理"""
        if not self.reader:
            messagebox.showerror("エラー", "OCR エンジンがまだ初期化中です。少しお待ちください。")
            return
        
        if self.is_processing:
            messagebox.showwarning("通知", "処理中です。お待ちください。")
            return
        
        thread = threading.Thread(target=self._process_image_thread, args=(file_path,), daemon=True)
        thread.start()
    
    def _process_image_thread(self, file_path):
        """スレッド内で画像を処理"""
        try:
            self.is_processing = True
            self.update_status("処理中...", self.colors['warning'])
            
            if not os.path.exists(file_path):
                raise FileNotFoundError("ファイルが見つかりません")
            
            self.display_thumbnail(file_path)
            
            img_array = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img_array is None:
                raise ValueError("画像ファイルを読み込めません")
            
            results = self.reader.readtext(img_array)
            extracted = '\n'.join([text[1] for text in results])
            
            self.extracted_text = extracted
            self.current_image_path = file_path
            
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", extracted)
            
            filename = Path(file_path).stem
            self.update_status(f"✓ 完了: {filename} ({len(extracted)}文字)", self.colors['success'])
            
            self.auto_save_text(file_path, extracted)
            
        except FileNotFoundError:
            messagebox.showerror("エラー", "ファイルが見つかりません")
            self.update_status("エラー", self.colors['error'])
        except Exception as e:
            messagebox.showerror("エラー", f"処理に失敗しました:\n{str(e)}")
            self.update_status("エラー", self.colors['error'])
        finally:
            self.is_processing = False
    
    def auto_save_text(self, image_path, text):
        """テキストを自動保存"""
        try:
            output_path = Path(image_path).parent / (Path(image_path).stem + "_txt.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"自動保存失敗: {e}")
    
    def copy_to_clipboard(self):
        """テキストをクリップボードにコピー"""
        if not self.extracted_text:
            messagebox.showwarning("警告", "コピーするテキストがありません")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.extracted_text)
        messagebox.showinfo("成功", "テキストをクリップボードにコピーしました")
    
    def save_text(self):
        """テキストをファイルに保存"""
        if not self.extracted_text:
            messagebox.showwarning("警告", "保存するテキストがありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.extracted_text)
                messagebox.showinfo("成功", "テキストを保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました:\n{str(e)}")
    
    def clear_text(self):
        """テキストをクリア"""
        self.text_widget.delete("1.0", tk.END)
        self.extracted_text = ""
        self.current_image_path = ""
        self.thumbnail_widget.config(text="画像を選択してください", image="")
        self.photo_image = None
        self.update_status("準備完了", self.colors['success'])
    
    def change_font_size(self, value=None):
        """テキストのフォントサイズを変更"""
        if self.font_size_var and self.text_widget:
            new_size = self.font_size_var.get()
            self.text_widget.config(font=("SF Mono", new_size))
            if self.size_display:
                self.size_display.config(text=str(new_size))


if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
        app = OCRApp(root)
        root.mainloop()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()