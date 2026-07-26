import streamlit as st
import streamlit.components.v1 as components
# 1. Global Page Config MUST be the very first Streamlit command
st.set_page_config(
    page_title="DelegateAI",
    page_icon="⌘",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_premium_ui_and_voice():
    """
    Injects the DelegateAI Design System (tokens + components) and the
    Voice Recognition Widget. Pure presentation layer — no business logic.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* =========================================
           DESIGN TOKENS
           ========================================= */
        :root {
            --bg: #0D1117;
            --surface: #161B22;
            --surface-2: #1C2128;
            --surface-3: #21262D;
            --border: #30363D;
            --border-soft: rgba(48, 54, 61, 0.6);
            --accent: #3B82F6;
            --accent-2: #1D4ED8;
            --accent-soft: rgba(59, 130, 246, 0.12);
            --success: #22C55E;
            --success-soft: rgba(34, 197, 94, 0.12);
            --danger: #EF4444;
            --danger-soft: rgba(239, 68, 68, 0.12);
            --warning: #F59E0B;
            --warning-soft: rgba(245, 158, 11, 0.12);
            --text-1: #F0F6FC;
            --text-2: #C9D1D9;
            --text-3: #8B949E;
            --text-4: #6E7681;

            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 20px;

            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-5: 20px;
            --space-6: 24px;
            --space-8: 32px;

            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.18);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.22);
            --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.28);
            --shadow-glow: 0 0 0 1px rgba(59, 130, 246, 0.25), 0 8px 24px rgba(59, 130, 246, 0.12);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, sans-serif !important;
            color: var(--text-2) !important;
        }
        .stApp, [data-testid="stHeader"] {
            background-color: var(--bg) !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }

        h1, h2, h3, h4, h5, h6 {
            font-weight: 600 !important;
            letter-spacing: -0.025em !important;
            color: var(--text-1) !important;
        }

        footer, .stDeployButton, #MainMenu { display: none !important; }

        .block-container {
            padding-top: 2rem !important;
            max-width: 1280px !important;
        }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-4); }

        /* =========================================
           SIDEBAR
           ========================================= */
        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

        .sidebar-brand {
            padding: 22px 20px 18px 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .sidebar-brand-icon {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
            color: #FFFFFF;
            width: 34px;
            height: 34px;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 17px;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
            flex-shrink: 0;
        }
        .sidebar-brand-text {
            font-weight: 700;
            font-size: 16px;
            letter-spacing: -0.01em;
            color: var(--text-1);
            line-height: 1.1;
        }
        .sidebar-brand-sub {
            font-size: 11px;
            color: var(--text-3);
            font-weight: 500;
            margin-top: 2px;
        }

        .sidebar-section-label {
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-4);
            padding: 0 20px;
            margin: 18px 0 6px 0;
        }

        /* Streamlit-native nav styling */
        [data-testid="stSidebarNav"] { padding-top: 4px !important; }
        [data-testid="stSidebarNav"] ul { padding: 0 12px !important; }
        [data-testid="stSidebarNav"] li { margin-bottom: 2px !important; }
        [data-testid="stSidebarNav"] a {
            border-radius: var(--radius-md) !important;
            padding: 9px 12px !important;
            transition: background-color 0.15s ease, color 0.15s ease !important;
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            color: var(--text-2) !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: var(--surface-2) !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: var(--accent-soft) !important;
            box-shadow: inset 2.5px 0 0 var(--accent);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: var(--text-1) !important;
            font-weight: 600 !important;
        }

        .sidebar-footer {
            margin-top: auto;
            padding: 14px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11.5px;
            color: var(--text-3);
        }

        /* =========================================
           GLASS TOP BAR
           ========================================= */
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: rgba(22, 27, 34, 0.7);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
        }
        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-3);
            background: var(--bg);
            padding: 6px 14px;
            border-radius: 20px;
            border: 1px solid var(--border);
        }
        .status-dot {
            width: 7px;
            height: 7px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
            animation: pulse 2s infinite;
        }

        /* =========================================
           SECTION LABELS / CARDS
           ========================================= */
        .section-label {
            font-size: 11.5px;
            color: var(--text-3);
            margin-bottom: 12px;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.06em;
        }
        .glass-card {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: var(--space-5);
            box-shadow: var(--shadow-sm);
        }
        .glass-card-tight { padding: var(--space-4); }

        /* Badges / pills */
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        .pill-success { background: var(--success-soft); color: var(--success); border: 1px solid rgba(34,197,94,0.25); }
        .pill-danger  { background: var(--danger-soft); color: var(--danger); border: 1px solid rgba(239,68,68,0.25); }
        .pill-warning { background: var(--warning-soft); color: var(--warning); border: 1px solid rgba(245,158,11,0.25); }
        .pill-neutral { background: var(--surface-3); color: var(--text-3); border: 1px solid var(--border); }
        .pill-accent  { background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(59,130,246,0.25); }

        /* Insight / stat rows */
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-soft);
            font-size: 13px;
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-row-label { color: var(--text-3); font-weight: 500; }
        .stat-row-value { color: var(--text-1); font-weight: 600; }

        /* =========================================
           KPI METRIC CARDS
           ========================================= */
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface) 100%) !important;
            border: 1px solid var(--border) !important;
            padding: 18px 20px !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-sm) !important;
            transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease !important;
        }
        [data-testid="stMetric"]:hover {
            border-color: var(--accent) !important;
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-glow) !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-3) !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.7rem !important;
            margin-bottom: 6px !important;
        }
        [data-testid="stMetricValue"] {
            color: var(--text-1) !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
            letter-spacing: -0.03em !important;
        }
        [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

        /* =========================================
           CHAT BUBBLES
           ========================================= */
        [data-testid="stChatMessage"] {
            border-radius: var(--radius-lg) !important;
            padding: 1.1rem 1.4rem !important;
            margin-bottom: 0.85rem !important;
            background-color: transparent !important;
            animation: fadeIn 0.25s ease-in forwards;
        }
        [data-testid="stChatMessage"]:nth-child(even) {
            background-color: var(--surface-2) !important;
            border: 1px solid var(--border) !important;
        }
        [data-testid="stChatMessage"]:nth-child(odd) {
            border-left: 3px solid var(--accent) !important;
            background-color: rgba(22, 27, 34, 0.4) !important;
            border-top: 1px solid var(--border) !important;
            border-right: 1px solid var(--border) !important;
            border-bottom: 1px solid var(--border) !important;
            padding-left: 1.6rem !important;
        }
        [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
            box-shadow: 0 0 0 2px var(--surface), 0 0 0 3px var(--border) !important;
        }

        /* =========================================
           CHAT COMPOSER & VOICE MIC
           ========================================= */
        [data-testid="stChatInput"] {
            border-radius: 20px !important;
            border: 1px solid var(--border) !important;
            background-color: var(--surface) !important;
            box-shadow: var(--shadow-lg) !important;
            position: relative !important;
            overflow: visible !important;
        }
        [data-testid="stChatInput"] > div {
            background-color: transparent !important;
            border: none !important;
            z-index: 1 !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--accent) !important;
        }
        [data-testid="stChatInputTextArea"] {
            padding-right: 85px !important;
            color: var(--text-1) !important;
            font-size: 14px !important;
            background: transparent !important;
        }

        /* Containers used as cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius-lg) !important;
            border-color: var(--border) !important;
            background-color: var(--surface-2) !important;
            transition: border-color 0.15s ease, transform 0.15s ease !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #3d4552 !important;
        }

        /* Expanders as call-history cards */
        [data-testid="stExpander"] {
            border-radius: var(--radius-lg) !important;
            border: 1px solid var(--border) !important;
            background-color: var(--surface-2) !important;
            overflow: hidden;
            margin-bottom: 10px !important;
        }
        [data-testid="stExpander"] summary {
            font-weight: 500 !important;
            padding: 12px 16px !important;
        }

        /* BUTTONS */
        .stButton>button {
            border-radius: var(--radius-md) !important;
            font-weight: 500 !important;
            border: 1px solid var(--border) !important;
            background: var(--surface-2) !important;
            color: var(--text-1) !important;
            transition: all 0.15s ease !important;
        }
        .stButton>button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }
        .stButton>button:active { transform: translateY(0); }

        /* Alerts (empty states) */
        [data-testid="stAlert"] {
            border-radius: var(--radius-lg) !important;
            border: 1px solid var(--border) !important;
            background-color: var(--surface-2) !important;
        }

        [data-testid="stChatInputSubmitButton"] { color: var(--accent) !important; }

        hr, [data-testid="stDivider"] { border-color: var(--border) !important; opacity: 0.7 !important; }

        /* KEYFRAMES */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        @keyframes micPulse {
            0% { transform: scale(1); filter: brightness(1); }
            50% { transform: scale(1.15); filter: brightness(1.4); }
            100% { transform: scale(1); filter: brightness(1); }
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar Branding Injection
    st.sidebar.html("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">⌘</div>
            <div>
                <div class="sidebar-brand-text">DelegateAI</div>
                <div class="sidebar-brand-sub">Call Operations Platform</div>
            </div>
        </div>
        <div class="sidebar-section-label">Workspace</div>
    """)

    # Sidebar footer (system status)
    st.sidebar.html("""
        <div class="sidebar-footer">
            <div class="status-dot"></div>
            Automation engine running
        </div>
    """)

    # Universal Voice Input Agent (Crash-Proof Singleton Execution)
    # Production-Grade Voice Subsystem (Singleton, MutationObserver, State Machine)
    st.iframe("""
    <script>
    const parentDoc = window.parent.document;
    const parentWindow = window.parent;

    // --- LIFECYCLE FIX ---
    // st.navigation remounts the main content area (and this component's
    // iframe) on every page switch, which destroys the JS realm that owned
    // the previous MutationObserver / SpeechRecognition instances. parentWindow
    // is the top browser window, so it survives navigation and still holds a
    // *reference* to the old DelegateVoiceSystem object even though its
    // observer has stopped firing. Trusting that stale reference (the old
    // "only init once" guard) is what caused the mic to silently stop
    // appearing on every page after the first. Instead, we always tear down
    // whatever is there (safely, in case it's already dead) and rebuild a
    // fresh, working system every time this script runs. injectButton()'s
    // existing duplicate-check keeps this from ever double-injecting.
    if (parentWindow.DelegateVoiceSystem) {
        const previousSystem = parentWindow.DelegateVoiceSystem;
        if (previousSystem.observer) {
            try { previousSystem.observer.disconnect(); } catch (e) { /* realm already gone */ }
        }
        if (previousSystem.recognition && previousSystem.currentState === previousSystem.STATES.LISTENING) {
            try { previousSystem.recognition.abort(); } catch (e) { /* realm already gone */ }
        }
    }

    {
        parentWindow.DelegateVoiceSystem = {
            STATES: {
                IDLE: 'IDLE',
                STARTING: 'STARTING',
                LISTENING: 'LISTENING',
                STOPPING: 'STOPPING'
            },
            currentState: 'IDLE',
            recognition: null,
            observer: null,
            isSupported: false,

            init: function() {
                console.log("[DelegateVoice] Initializing Voice Subsystem...");
                const SpeechRecognition = parentWindow.SpeechRecognition || parentWindow.webkitSpeechRecognition;
                
                if (!SpeechRecognition) {
                    console.warn("[DelegateVoice] Speech recognition not supported in this browser.");
                    this.isSupported = false;
                    this.startObserver();
                    return;
                }

                this.isSupported = true;
                this.recognition = new SpeechRecognition();
                this.recognition.continuous = false;
                this.recognition.lang = 'en-US';

                this.bindEvents();
                this.startObserver();
                this.setupCleanup();
                console.log("[DelegateVoice] Voice initialized successfully.");
            },

            bindEvents: function() {
                // Events are bound EXACTLY ONCE
                this.recognition.onstart = () => {
                    this.currentState = this.STATES.LISTENING;
                    console.log("[DelegateVoice] Recognition started.");
                    this.updateUI();
                };

                this.recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    console.log("[DelegateVoice] Transcript received:", transcript);
                    this.applyTextDynamically(transcript);
                };

                this.recognition.onerror = (event) => {
                    console.error("[DelegateVoice] Recognition error:", event.error);
                    this.currentState = this.STATES.IDLE;
                    this.updateUI();
                };

                this.recognition.onend = () => {
                    console.log("[DelegateVoice] Recognition stopped.");
                    this.currentState = this.STATES.IDLE;
                    this.updateUI();
                };
            },

            toggleRecording: function() {
                if (!this.isSupported) return;

                if (this.currentState === this.STATES.IDLE) {
                    try {
                        this.currentState = this.STATES.STARTING;
                        console.log("[DelegateVoice] Attempting to start recognition...");
                        this.recognition.start();
                    } catch (err) {
                        console.error("[DelegateVoice] Failed to start:", err);
                        this.currentState = this.STATES.IDLE;
                    }
                } else if (this.currentState === this.STATES.LISTENING) {
                    try {
                        this.currentState = this.STATES.STOPPING;
                        console.log("[DelegateVoice] Attempting to stop recognition...");
                        this.recognition.stop();
                    } catch (err) {
                        console.error("[DelegateVoice] Failed to stop:", err);
                        this.currentState = this.STATES.IDLE;
                    }
                } else {
                    console.log(`[DelegateVoice] Ignored click. System is currently ${this.currentState}.`);
                }
            },

            isVisible: function(el) {
                // A destroyed/replaced or off-screen (different page) node still matches the
                // selector but has no layout box. Filter those out so we never act on stale nodes.
                return !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            },

            getChatInputWrappers: function() {
                // The app can render more than one st.chat_input() (Agentic Chat, Analytics Agent,
                // and any future page). Always operate on the full, current set — never assume
                // there is exactly one.
                return Array.from(parentDoc.querySelectorAll('[data-testid="stChatInput"]'));
            },

            applyTextDynamically: function(transcript) {
                // Never hold stale DOM references. Find the currently VISIBLE input at this exact
                // millisecond — with multiple chat inputs across pages, only one is ever on-screen.
                const wrappers = this.getChatInputWrappers();
                const activeWrapper = wrappers.find((w) => this.isVisible(w)) || wrappers[0];
                if (!activeWrapper) {
                    console.warn("[DelegateVoice] Cannot apply text. Chat input destroyed.");
                    return;
                }

                const textarea = activeWrapper.querySelector('textarea');
                if (!textarea) return;

                const setter = Object.getOwnPropertyDescriptor(parentWindow.HTMLTextAreaElement.prototype, "value").set;
                const newText = textarea.value ? textarea.value + " " + transcript : transcript;
                
                setter.call(textarea, newText);
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                console.log("[DelegateVoice] Text successfully injected into Streamlit UI.");
            },

            updateUI: function() {
                // There is one shared recognition session, but potentially several injected
                // buttons across pages/reruns — keep all of them in sync, not just the first.
                const buttons = parentDoc.querySelectorAll('.voice-mic-btn');
                if (!buttons.length) return;

                buttons.forEach((btn) => {
                    if (this.currentState === this.STATES.LISTENING) {
                        btn.innerHTML = '🔴';
                        btn.style.animation = 'micPulse 1.5s infinite';
                        btn.style.color = '#EF4444';
                    } else {
                        btn.innerHTML = '🎙️';
                        btn.style.animation = 'none';
                        btn.style.color = 'inherit';
                    }
                });
            },

            injectButton: function(wrapper) {
                // Ensure no duplicate buttons are injected
                if (wrapper.querySelector('.voice-mic-btn')) return;

                const btn = parentDoc.createElement('button');
                btn.type = 'button';
                btn.className = 'voice-mic-btn';
                
                // Preserve existing CSS architecture
                btn.style.cssText = 'position: absolute; right: 48px; bottom: 11px; background: transparent; border: none; font-size: 18px; cursor: pointer; z-index: 99999; outline: none; transition: transform 0.2s ease; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; margin: 0; padding: 0;';

                if (this.isSupported) {
                    btn.innerHTML = '🎙️';
                    btn.title = "Click to dictate";
                    btn.onmouseover = () => btn.style.transform = 'scale(1.12)';
                    btn.onmouseout = () => btn.style.transform = 'scale(1)';
                    btn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.toggleRecording();
                    };
                } else {
                    btn.innerHTML = '🚫';
                    btn.title = "Voice input not supported in this browser.";
                    btn.style.opacity = "0.3";
                    btn.style.cursor = "not-allowed";
                }

                wrapper.style.position = 'relative';
                wrapper.appendChild(btn);
                console.log("[DelegateVoice] Microphone button injected.");
                
                // Sync UI state in case it was injected while engine is active
                this.updateUI();
            },

            injectAll: function() {
                // Scan every chat input currently in the document — Agentic Chat, Analytics
                // Agent, or any future page — and inject into whichever ones don't already
                // have a button. Runs on the initial check AND every subsequent mutation, so
                // a chat input that Streamlit destroys and recreates on a rerun/navigation
                // simply gets treated as "missing its button" again and re-injected.
                this.getChatInputWrappers().forEach((wrapper) => {
                    if (!wrapper.querySelector('.voice-mic-btn')) {
                        console.log("[DelegateVoice] Chat input detected without mic. Injecting.");
                        this.injectButton(wrapper);
                    }
                });
            },

            startObserver: function() {
                // Highly performant observer replacing setInterval. Keeps watching the document
                // for the lifetime of the tab — it is never disconnected except on page unload —
                // so it survives reruns, page navigation, and session state driven re-renders.
                this.observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        if (mutation.addedNodes.length > 0) {
                            this.injectAll();
                            break;
                        }
                    }
                });

                this.observer.observe(parentDoc.body, { childList: true, subtree: true });
                
                // Run an initial check just in case one or more chat inputs are already in the DOM
                this.injectAll();
            },

            setupCleanup: function() {
                parentWindow.addEventListener('beforeunload', () => {
                    console.log("[DelegateVoice] Cleaning up resources...");
                    if (this.observer) this.observer.disconnect();
                    if (this.recognition && this.currentState === this.STATES.LISTENING) {
                        console.log("[DelegateVoice] Recognition aborted due to unload.");
                        this.recognition.abort();
                    }
                });
            }
        };

        // Bootstrap the system
        parentWindow.DelegateVoiceSystem.init();
    }
    </script>
    """)

# Local imports
from pages.save_tasks import page_tasks
from pages.execute_calls import page_calls
from pages.dashboard import page_dashboard
from caller_agent import start_automation_engine

def main():
    inject_premium_ui_and_voice()
    
    if 'automation_started' not in st.session_state:
        start_automation_engine()
        st.session_state.automation_started = True
    
    pg = st.navigation([
        st.Page(page_tasks, title='Agentic Chat', icon='⚡'),
        st.Page(page_calls, title='Live Monitor', icon='📡'),
        st.Page(page_dashboard, title='Analytics', icon='📊')
    ])
    pg.run()

if __name__ == '__main__':
    main()