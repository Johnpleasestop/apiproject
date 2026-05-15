# TechBuddy - PC Builder AI Chat

A conversational AI desktop app that helps users design a custom PC build step by step. Powered by Google Gemini, built with Python and Tkinter, with SQLite conversation archiving.

---

## Features

- **Guided PC build flow** — TechBuddy walks users through use case, budget, peripherals, and aesthetics before recommending a build
- **Itemized parts list** — AI responds in a consistent format with per-component pricing, subtotal, tax, and total
- **Performance expectations** — Every build recommendation includes realistic FPS, render time, and multitasking estimates
- **Copy Parts List** — Extracts just the component names from the last AI response for easy pasting into [PCPartPicker](https://pcpartpicker.com)
- **Copy Full Chat** — Copies the entire conversation to clipboard
- **Conversation archive** — All messages are saved automatically to a local SQLite database (`buddyarchive.db`)
- **Token-efficient** — Filler word compression and automatic history trimming keep API usage low

---

## Requirements

- Python 3.8+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)

### Dependencies

```
google-generativeai
tkinter (included in standard Python on Windows/macOS)
```

Install dependencies:

```bash
pip install google-generativeai
```

> **Linux users:** If `tkinter` is missing, install it with `sudo apt install python3-tk`

---

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Create your API key file**

   Create a file named `apikey.txt` in the same folder as the script and paste your Gemini API key inside (nothing else, just the key).

   ```
   your-api-key-here
   ```

3. **Run the app**
   ```bash
   python apigithub.py
   ```

---

## Usage

1. Click **Load API Key** — the app will auto-detect `apikey.txt` if it's in the same directory, or open a file picker
2. Optionally list any parts you already own in the **Existing Parts** box (or type `all` / `none`)
3. Type your message in the chat box and press **Enter** or click **Send**
4. TechBuddy will ask about your use case, budget, and preferences before recommending a build
5. Once a build is recommended, use **Copy Parts List** to grab component names for PCPartPicker, or **Copy Full Chat** to save the whole conversation

---

## Project Structure

```
├── apigithub.py       # Main application
├── apikey.txt         # Your Gemini API key (not committed to git)
└── buddyarchive.db    # SQLite conversation archive (auto-created on first run)
```

---

## Notes

- `buddyarchive.db` is created automatically on first launch and persists across sessions
- Resetting the chat clears the UI but keeps all messages in the database
- Conversation history is trimmed every 5 turns to reduce token usage (only the most recent exchanges are sent to the API)
- The **Copy Parts List** button works best when the AI has just provided a full build recommendation

---

## Authors

Hogan Polston, Emmanuel Aroh, John Mitchell

---

## License

This project is for educational use.
