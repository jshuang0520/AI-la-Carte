class Constants:
    # Language codes
    LANG_EN = 'en'
    LANG_ES = 'es'
    
    # Database
    DB_NAME = 'ai_la_carte.db'
    DB_TABLE_DATA = 'data'
    
    # File paths
    CONFIG_FILE = 'config.json'
    LOG_DIR = 'logs'
    LOG_FILE = 'app.log'
    
    # Default values
    DEFAULT_LANGUAGE = 'en'
    DEFAULT_DISTANCE_THRESHOLD = 1.0
    DEFAULT_LOG_LEVEL = 'INFO'
    
    # Error messages
    ERROR_DB_CONNECTION = "Database connection error"
    ERROR_TRANSLATION = "Translation error"
    ERROR_PARSING = "Parsing error"
    ERROR_FILTERING = "Filtering error"
    
    # Success messages
    SUCCESS_DB_STORE = "Data stored successfully"
    SUCCESS_TRANSLATION = "Translation completed successfully"
    SUCCESS_PARSING = "Parsing completed successfully"
    SUCCESS_FILTERING = "Filtering completed successfully" 