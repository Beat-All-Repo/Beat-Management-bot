import os


class Config(object):
    LOGGER = True

    # ── Telegram API credentials (required) ───────────────────────────────────
    # Get from https://my.telegram.org/apps
    API_ID = int(os.environ.get("API_ID", 6))
    API_HASH = os.environ.get("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e")

    # Bot token from @BotFather
    TOKEN = os.environ.get("TOKEN", "")

    # ── Owner / sudo users ────────────────────────────────────────────────────
    # Your Telegram numeric user ID (must be integer)
    OWNER_ID = int(os.environ.get("OWNER_ID", 1356469075))

    # Comma-separated list of sudo user IDs  e.g. "123,456,789"
    DRAGONS = set(int(x) for x in os.environ.get("DRAGONS", "").split(",") if x.strip())

    # Dev users (highest privilege tier)
    DEV_USERS = set(int(x) for x in os.environ.get("DEV_USERS", "").split(",") if x.strip())

    # Support / demon users
    DEMONS = set(int(x) for x in os.environ.get("DEMONS", "").split(",") if x.strip())

    # Tiger users
    TIGERS = set(int(x) for x in os.environ.get("TIGERS", "").split(",") if x.strip())

    # Whitelist / wolf users
    WOLVES = set(int(x) for x in os.environ.get("WOLVES", "").split(",") if x.strip())

    # ── Database (required — at least one) ───────────────────────────────────
    # PostgreSQL URL from elephantsql.com, supabase, etc.
    # Example: postgresql://user:pass@host/dbname
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # MongoDB URI from cloud.mongodb.com / Atlas
    # Example: mongodb+srv://user:pass@cluster0.mongodb.net/dbname
    MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "")

    # ── Support / community links ─────────────────────────────────────────────
    # Username of your support group (without @)
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "DevilsHeavenMF")

    # Event log channel ID (integer) or leave empty
    _event_logs = os.environ.get("EVENT_LOGS", "")
    EVENT_LOGS = int(_event_logs) if _event_logs.strip() else None

    # ── Optional API keys ─────────────────────────────────────────────────────
    # Currency converter — https://www.alphavantage.co/support/#api-key
    CASH_API_KEY = os.environ.get("CASH_API_KEY", "")

    # Timezone DB — https://timezonedb.com/api
    TIME_API_KEY = os.environ.get("TIME_API_KEY", "")

    # Wallpaper API key — https://alphacoders.com/api
    WALL_API_KEY = os.environ.get("WALL_API_KEY", "")

    # ── Bot appearance / UX ───────────────────────────────────────────────────
    # Telegraph image URL shown on /start
    START_IMG = os.environ.get(
        "START_IMG",
        "https://telegra.ph/file/ec17880d61180d3312d6a.jpg",
    )

    # Comma-separated list of start image URLs (random pick each time)
    START_PICS = [
        p.strip()
        for p in os.environ.get(
            "START_PICS",
            "https://telegra.ph/file/ec17880d61180d3312d6a.jpg",
        ).split(",")
        if p.strip()
    ]

    # Comma-separated list of help image URLs
    HELP_PICS = [
        p.strip()
        for p in os.environ.get("HELP_PICS", "https://ibb.co/BVccVQZq").split(",")
        if p.strip()
    ]

    # Anime / updates channel link
    ANIME_CHANNEL = os.environ.get("ANIME_CHANNEL", "https://t.me/Beat_Hindi_Dubbed")

    # Contact admin link
    CONTACT_ADMIN = os.environ.get("CONTACT_ADMIN", "")

    # Whether to show the info picture
    INFOPIC = bool(os.environ.get("INFOPIC", True))

    # ── Behaviour flags ───────────────────────────────────────────────────────
    # Allow bot in group chats?
    ALLOW_CHATS = bool(os.environ.get("ALLOW_CHATS", True))

    # Allow commands with ! and ? prefix in addition to /?
    ALLOW_EXCL = bool(os.environ.get("ALLOW_EXCL", True))

    # Auto-delete command messages?
    DEL_CMDS = bool(os.environ.get("DEL_CMDS", True))

    # Strictly enforce global bans?
    STRICT_GBAN = bool(os.environ.get("STRICT_GBAN", True))

    # Temp download directory
    TEMP_DOWNLOAD_DIRECTORY = os.environ.get("TEMP_DOWNLOAD_DIRECTORY", "./")

    # Thread-pool worker count
    WORKERS = int(os.environ.get("WORKERS", 8))

    # ── Module loading ────────────────────────────────────────────────────────
    # List of extra module names to load (comma-separated)
    LOAD = [x.strip() for x in os.environ.get("LOAD", "").split(",") if x.strip()]

    # List of module names to skip (comma-separated)
    NO_LOAD = [x.strip() for x in os.environ.get("NO_LOAD", "").split(",") if x.strip()]

    # ── Group blacklist ───────────────────────────────────────────────────────
    # Comma-separated list of group IDs the bot should refuse to work in
    BL_CHATS = [
        int(x.strip())
        for x in os.environ.get("BL_CHATS", "").split(",")
        if x.strip()
    ]

    # ── Web / health-check server (used on Render free tier) ─────────────────
    # Port for the keep-alive HTTP server; Render injects PORT automatically
    PORT = int(os.environ.get("PORT", 8080))

    # Public URL of your Render service (used for webhook mode, optional)
    # Example: https://your-bot-name.onrender.com
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
