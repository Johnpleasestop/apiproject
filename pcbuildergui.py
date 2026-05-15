"""
PC Builder Conversational AI - Tkinter GUI with Chat Interface
Updated with Smart Copy and Full Chat Export features.
Now with SQLite3 database storage.
"""

import google.generativeai as genai
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re  # Added for parsing parts lists
import sqlite3
from datetime import datetime

class PCBuilderChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Builder AI Chat")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)  # Set minimum window size
        
        self.api_key_loaded = False
        self.chat = None
        self.model = None
        self.turn_count = 0
        
        # Initialize database
        self.init_database()
        
        self.setup_ui()
        
    def init_database(self):
        """Initialize SQLite database for storing conversations"""
        try:
            self.db_conn = sqlite3.connect('buddyarchive.db')
            self.db_cursor = self.db_conn.cursor()
            
            # Create table if it doesn't exist
            self.db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            ''')
            self.db_conn.commit()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            # Continue anyway - app can still work without database
            self.db_conn = None
            self.db_cursor = None
    
    def save_to_database(self, sender, message):
        """Save a message to the database"""
        if not self.db_conn or not self.db_cursor:
            return  # Skip if database isn't available
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db_cursor.execute(
                'INSERT INTO conversations (timestamp, sender, message) VALUES (?, ?, ?)',
                (timestamp, sender, message)
            )
            self.db_conn.commit()
            
        except sqlite3.Error as e:
            # Don't pop up error - just log it silently so chat isn't interrupted
            print(f"Database save error: {str(e)}")
        
    def setup_ui(self):
        """Create the UI layout"""
        
        # --- API Key Section ---
        api_frame = ttk.LabelFrame(self.root, text="Step 1: Load API Key")
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(api_frame, text="Load API Key", command=self.load_api_key).pack(side="left", padx=10, pady=5)
        
        self.api_status_var = tk.StringVar(value="No Key Loaded")
        self.api_status_label = ttk.Label(api_frame, textvariable=self.api_status_var, foreground="red")
        self.api_status_label.pack(side="left", padx=10, pady=5)
        
        # --- Parts Ownership Section (Collapsed) ---
        parts_frame = ttk.LabelFrame(self.root, text="Step 2: Existing Parts & Peripherals")
        parts_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(parts_frame, text="Already own parts? (List them, type 'all' for all peripherals, or 'none')", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=5)
        
        self.owned_parts_text = tk.Text(parts_frame, wrap="word", height=2, font=("Segoe UI", 10), state="disabled")
        self.owned_parts_text.pack(fill="x", padx=10, pady=(0,5))
        
        # --- Chat Section (Takes up most space) ---
        chat_frame = ttk.LabelFrame(self.root, text="Step 3: Chat with TechBuddy")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Control buttons at TOP (always visible)
        control_frame = ttk.Frame(chat_frame)
        control_frame.pack(fill="x", padx=5, pady=5, side="top")
        control_frame.pack_propagate(False)
        control_frame.configure(height=40)
        
        # Button Styling
        button_style = ttk.Style()
        button_style.configure("Large.TButton", font=("Segoe UI", 8, "bold"), padding=10)
        
        # Reset Button
        self.reset_button = ttk.Button(control_frame, text="Reset", command=self.reset_conversation, 
                                       state="disabled", style="Large.TButton", width=8)
        self.reset_button.pack(side="left", padx=5, fill="y")
        
        # --- NEW BUTTONS START ---
        self.copy_all_button = ttk.Button(control_frame, text="Copy Full Chat", command=self.copy_full_chat,
                                     state="disabled", style="Large.TButton", width=15)
        self.copy_all_button.pack(side="left", padx=5, fill="y")

        self.copy_parts_button = ttk.Button(control_frame, text="Copy Parts List", command=self.copy_specs,
                                      state="disabled", style="Large.TButton", width=15)
        self.copy_parts_button.pack(side="left", padx=5, fill="y")
        # --- NEW BUTTONS END ---
        
        ttk.Label(control_frame, text="Press Enter or click Send", 
                 font=("Segoe UI", 9), foreground="gray").pack(side="left", padx=10)
        
        # Input frame AT BOTTOM - always visible, prevent wrapping
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", padx=5, pady=(5, 10), side="bottom")
        input_frame.pack_propagate(False)  # Prevent frame from shrinking
        input_frame.configure(height=50)  # Fixed height to prevent collapse
        
        self.message_entry = ttk.Entry(input_frame, font=("Segoe UI", 10), state="disabled")
        self.message_entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Create larger button with styling - fixed width prevents wrapping
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message, 
                                      state="disabled", style="Large.TButton", width=10)
        self.send_button.pack(side="left", fill="y")
        
        # Chat history display - prioritize this for vertical space (in the middle)
        chat_scroll_frame = ttk.Frame(chat_frame)
        chat_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(chat_scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.chat_display = tk.Text(chat_scroll_frame, wrap="word", font=("Segoe UI", 10), 
                                    state="disabled", bg="#f5f5f5", yscrollcommand=scrollbar.set)
        self.chat_display.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.chat_display.yview)
        
        # Configure text tags for styling
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("ai", foreground="#009900", font=("Segoe UI", 10, "bold"))
    
    def load_api_key(self):
        """Load API key from file"""
        # Try default file first
        if os.path.exists("apikey.txt"):
            filepath = "apikey.txt"
        else:
            # Open file dialog
            filepath = filedialog.askopenfilename(
                title="Select API Key File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                key = f.read().strip()
            
            if not key:
                raise ValueError("The file is empty.")
            
            # Configure Gemini
            genai.configure(api_key=key)
            
            # Create model
            self.model = self.create_sales_consultant()
            self.chat = self.model.start_chat(history=[])
            
            self.api_key_loaded = True
            self.api_status_var.set(f"Key Loaded: {os.path.basename(filepath)}")
            self.api_status_label.config(foreground="green")
            
            # Enable controls
            self.unlock_controls()
            
            # Show initial greeting
            self.display_message("TechBuddy", "What will you use this PC for?")
            
            messagebox.showinfo("Success", "API Key loaded! You can now start chatting.")
            
        except FileNotFoundError:
            messagebox.showerror("File Error", f"Could not find file: {filepath}")
        except PermissionError:
            messagebox.showerror("Permission Error", f"No permission to read file: {filepath}")
        except ValueError as ve:
            messagebox.showerror("API Error", str(ve))
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to load key: {str(e)}")
    
    def create_sales_consultant(self):
        """Initialize AI with ultra-concise system instructions"""
        system_instruction = """PC build expert. Direct responses only.

RULES:
- 2 sentences max unless listing parts or performance analysis
- No pleasantries, greetings, or filler
- Ask 1 question at time
- Budget >$1200: ask RGB/watercooling preference
- Explain benefits briefly

FORMAT FOR PARTS LIST:
When recommending parts, use this exact format:
CPU: [Name] - $[price]
GPU: [Name] - $[price]
Motherboard: [Name] - $[price]
RAM: [Name] - $[price]
Storage: [Name] - $[price]
PSU: [Name] - $[price]
Case: [Name] - $[price]
Cooler: [Name] - $[price]
[Any other parts needed]

Then show:
Subtotal: $[amount]
Tax (8%): $[amount]
Total: $[amount]

PERFORMANCE ANALYSIS (Required after every build):
After showing pricing, provide a "Performance Expectations" section:
- Describe specific performance for their use case
- Include frame rates for gaming (1080p/1440p/4K if applicable)
- Rendering times for video editing
- Multitasking capabilities for productivity
- Be specific with numbers and realistic expectations

Example:
"Performance Expectations:
This build will handle 1440p gaming at 100+ FPS in most AAA titles at high settings. Expect 144+ FPS in competitive games like Valorant and CS2. Video editing in 4K will be smooth with export times around 2x realtime speed."

- Use newlines for readability, never markdown bold/italics
- No ** or __ formatting

INITIAL QUESTIONS:
1. First ask about use case (be specific - what games? what resolution? what programs?)
2. Then ask budget
3. Then check if they need peripherals (monitor, keyboard, mouse) - they'll tell you what they already own
4. If budget allows, ask about aesthetics

PRICING RULES:
- Show individual price for EVERY component
- Calculate accurate subtotal by adding all parts
- Calculate 8% tax on subtotal
- Show final total with tax included
- If they already own parts, don't include those in pricing

FLOW: use case → budget → check peripherals → aesthetics (if applicable) → recommend with itemized pricing → show subtotal/tax/total → performance analysis

TONE: Professional, direct, no-nonsense, but detailed on performance expectations
"""
        
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_instruction
        )
        
        return model
    
    def unlock_controls(self):
        """Enable chat controls"""
        self.owned_parts_text.config(state="normal")
        self.message_entry.config(state="normal")
        self.send_button.config(state="normal")
        self.reset_button.config(state="normal")
        # Enable new copy buttons
        self.copy_all_button.config(state="normal")
        self.copy_parts_button.config(state="normal")
    
    def display_message(self, sender, message):
        """Display a message in the chat window and save to database"""
        self.chat_display.config(state="normal")
        
        if sender == "You":
            self.chat_display.insert(tk.END, f"{sender}: ", "user")
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "ai")
        
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")
        
        # Save to database
        self.save_to_database(sender, message)
    
    def send_message(self):
        """Send user message to AI"""
        if not self.api_key_loaded:
            messagebox.showwarning("No API Key", "Please load your API key first.")
            return
        
        user_message = self.message_entry.get().strip()
        
        if not user_message:
            return
        
        # Display user message
        self.display_message("You", user_message)
        self.message_entry.delete(0, tk.END)
        
        # If first message and owned parts specified, append that info
        if self.turn_count == 0:
            owned_parts = self.owned_parts_text.get("1.0", tk.END).strip()
            if owned_parts:
                # Interpret 'all' or 'none'
                if owned_parts.lower() == 'all':
                    context = f"{user_message}\n\nNote: I already own all necessary peripherals (monitor, keyboard, mouse, headset, etc)."
                elif owned_parts.lower() == 'none':
                    context = f"{user_message}\n\nNote: I'm starting completely from scratch, need everything including peripherals."
                else:
                    context = f"{user_message}\n\nNote: I already own: {owned_parts}"
                
                user_message = context
        
        # Compress user input
        compressed_message = self.compress_user_input(user_message)
        
        # Send to AI
        try:
            response = self.chat.send_message(compressed_message)
            self.display_message("TechBuddy", response.text)
            
            self.turn_count += 1
            
            # Auto-compress history every 5 turns (silent)
            if self.turn_count >= 5:
                self.chat._history = self.compress_history(self.chat._history)
                self.turn_count = 0
            
        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg or "quota" in error_msg.lower():
                messagebox.showerror("Rate Limit", 
                    "Rate limit reached. Wait a few minutes or use a different API key.\n\n"
                    "Free tier: 15 requests/minute, 1500 requests/day")
            elif "API_KEY" in error_msg.upper() or "INVALID" in error_msg.upper():
                messagebox.showerror("API Key Error", 
                    "Invalid API key. Please check your apikey.txt file.")
            else:
                messagebox.showerror("Error", f"AI Error: {error_msg}")
    
    def reset_conversation(self):
        """Reset the chat (UI only - database keeps messages)"""
        if messagebox.askyesno("Reset", "Clear conversation and start fresh?\n\n(Note: Messages will remain saved in database)"):
            self.chat = self.model.start_chat(history=[])
            self.turn_count = 0
            
            self.chat_display.config(state="normal")
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state="disabled")
            
            self.display_message("TechBuddy", "What will you use this PC for?")
    
    def compress_user_input(self, text):
        """Remove filler words to save tokens"""
        fillers = ['um', 'uh', 'like', 'you know', 'i mean', 'basically', 'actually']
        compressed = text.lower()
        for filler in fillers:
            compressed = compressed.replace(filler, '')
        compressed = ' '.join(compressed.split())
        
        if len(compressed) < len(text) * 0.8:
            return compressed
        return text
    
    def compress_history(self, history, max_turns=6):
        """Keep only recent conversation"""
        if len(history) > max_turns * 2:
            return [history[0]] + history[-(max_turns * 2):]
        return history

    def copy_full_chat(self):
        """Copy the entire conversation history to clipboard"""
        content = self.chat_display.get("1.0", tk.END).strip()
        if content:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                messagebox.showinfo("Copied", "Full conversation copied to clipboard!")
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy: {str(e)}")
        else:
            messagebox.showinfo("Empty", "Nothing to copy yet.")

    def copy_specs(self):
        """Extracts parts from the last AI message for easy pasting into PCPartPicker"""
        if not self.chat or not self.chat.history:
            messagebox.showinfo("No Messages", "No conversation history yet.")
            return

        # Get the last message from the AI
        last_response = ""
        for message in reversed(self.chat.history):
            if message.role == "model":
                last_response = message.parts[0].text
                break
        
        if not last_response:
            messagebox.showinfo("No AI Response", "No AI messages found.")
            return

        # Regex to find lines like "CPU: [Name] - $[Price]"
        # We capture just the Type and Name, ignoring the price
        # This makes it much easier to paste into search bars
        pattern = r"([A-Za-z\s]+): (.+) - \$"
        matches = re.findall(pattern, last_response)

        if matches:
            # Create a clean list: "Part Type: Part Name"
            clipboard_text = ""
            for part_type, part_name in matches:
                clipboard_text += f"{part_type}: {part_name}\n"
            
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_text)
                messagebox.showinfo("Copied", "Parts list copied!\nYou can now paste names directly into PCPartPicker.")
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy: {str(e)}")
        else:
            # Fallback: If no strict list found, copy the whole last message
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(last_response)
                messagebox.showinfo("Copied", "Could not detect strict list, copied full response instead.")
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy: {str(e)}")
    
    def __del__(self):
        """Cleanup database connection on exit"""
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass

def main():
    root = tk.Tk()
    app = PCBuilderChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
