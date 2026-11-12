# Application constants

APP_NAME = "Merisio"
APP_VERSION = "1.6.0"
FILE_EXTENSION = ".merisio"
FILE_FILTER = "Merisio Projects (*.merisio);;All Files (*)"
# The Open dialog also lists *.asip: Save As wrongly gave new projects that
# extension in v1.1.0 to v1.6.0 (GitHub issue #1), so those files must stay findable.
OPEN_FILE_FILTER = "Merisio Projects (*.merisio *.asip);;All Files (*)"
MSD_FILE_EXTENSION = ".msd"
MSD_FILE_FILTER = "MSD Files (*.msd);;All Files (*)"

# Data types for dictionary
DATA_TYPES = [
    "INT",
    "BIGINT",
    "SMALLINT",
    "VARCHAR",
    "CHAR",
    "TEXT",
    "BOOLEAN",
    "DATE",
    "TIME",
    "TIMESTAMP",
    "DECIMAL",
    "FLOAT",
    "DOUBLE",
]

# Cardinality values
CARDINALITY_MIN = ["0", "1"]
CARDINALITY_MAX = ["1", "N"]

# Canvas settings
ENTITY_WIDTH = 120
ENTITY_HEIGHT = 80
ASSOCIATION_WIDTH = 100
ASSOCIATION_HEIGHT = 60

# Colors
ENTITY_COLOR = "#E3F2FD"
ENTITY_BORDER = "#1976D2"
ASSOCIATION_COLOR = "#FFF3E0"
ASSOCIATION_BORDER = "#F57C00"
LINK_COLOR = "#000000"  # Black
SELECTED_COLOR = "#FF5722"
