# Minesweeper Solver

Minesweeper Solver is an automated tool designed to assist players in solving Minesweeper on the [Minesweeper Online website](https://minesweeper.online) developed in Python using OpenCV, NumPy and Pyatuogui. The project consists of two main components:

- **Hint Overlay** - Displays a visual guide indicating safe, dangerous, and incorrectly flagged tiles.

    **Showcase**: 
    
    ![Hint Showcase](assets/hint_showcase.gif)

- **Bot** - Automates tile clicks, solving the game for you with adjustable speed.

    **Showcase**: 
    
    ![Bot Showcase](assets/bot_showcase.gif)


> **Disclaimer:** Using the bot, especially with really small delays, may result in an IP ban from Minesweeper Online. Use it at your own risk.

## Features

- **Automatic Field Detection**: Identifies and extracts the Minesweeper grid from the screen.

- **Custom Calibration**: Adjusts tile and field padding for various screen resolutions.

- **Hint System**: Provides a visual overlay to guide manual play.

- **Automated Bot**: Clicks tiles intelligently to win the game.

- **Turbo Mode**: Allow the bot to click way faster but increases the risk of misclicking if windows are switched.

## Prerequisites

Ensure you have the following installed:

- **Python 3.8+**

- **Required dependencies**:


        pip install -r requirements.txt


## Before Usage

### Configuration

Before using the solver, you may need to adjust certain settings in the `config.env` file. These settings control how the bot and hint overlay behave.

#### General Settings

- `MAIN_COLOR`
    - The RGB color of the Minesweeper field background (The most common color on the field). 
    
    - Default is set for **light mode** on Minesweeper Online (198,198,198).


- `TILE_PADDING`
    - The spacing between individual tiles.
    
    - This is automatically adjusted during [Calibration](#2-calibration).

- `FIELD_PADDING`
    - The boundary around the Minesweeper grid.
    
    - Also adjusted during [Calibration](#2-calibration).

#### Bot-Specific Settings

- `SCREEN_SCALING`
    - If using **Windows** leave it at `1`

    - Else adjusts for your **OS display scaling** (e.g., `1.25`, `1.5`).
    
    - Required for accurate clicking.

- `CLICK_DELAY`
    - The delay (in milliseconds) between consecutive clicks.
    
    - Increasing this makes the bot slower but more controlled.

- `TURBO_MODE`
    - Enables batch clicking, greatly improving performance.
    
    - Can be riskier if you switch windows during execution.
    
    - Set to `0` to disable or `1` to enable.

#### Hint-Specific Settings

- `CHECK_DELAY`
    - Time (in integer seconds) between hint updates.
    
    - A lower value provides faster updates but may use more CPU.

### 2. Calibration

You must run `calibrate.py` before using any other scripts to ensure they function correctly.

Calibration determines `FIELD_PADDING` and `TILE_PADDING` in `config.env`, as these values vary depending on screen resolution and zoom level.

#### Running Calibration

    python calibrate.py

1. **Prepare Your Screen**:

    - Open [Minesweeper Online](https://minesweeper.online) on the **right half** of your screen.

    - Ensure that **at least one tile is uncovered** for proper detection.

2. **Adjust the Grid Overlay**:

    - A window will open displaying an overlayed **green grid**.

    - Use the following controls to align the green grid with the Minesweeper tiles:

    **Controls:**
    - `W` → Increase **field padding** (moves the whole grid right and down)
    
    - `S` → Decrease **field padding** (moves the whole grid left and up)
    
    - `A` → Decrease **tile padding** (decreases the size of a single tile)
    
    - `D` → Increase **tile padding** (increases the size of a single tile)
    
    - `Enter` → Save the settings and exit

    **Showcase:**

    ![Calibration Showcase](assets/calibration_showcase.gif)

3. **Completing Calibration**:
    - Once the grid is correctly aligned, press `Enter`.
    
    - The updated values will be saved in `config.env`.
    
    - You can now proceed with using the **Hint Overlay** or **Bot**.


## Usage

### 1. Running the Hint Overlay

The hint tool scans the Minesweeper board and displays a visual overlay indicating **safe**, **dangerous**, and **flagged** tiles.

    python hint.py

- The hint overlay only scans the **right half** of your screen.

- The **entire Minesweeper field** must be on the right side.

- The **hint window with the overlay** should be moved to the **left half** of the screen.

The overlay colors indicate:

- **Green**: Safe tiles

- **Red**: Unflagged tiles with a mine

- **Yellow**: Incorrectly flagged tiles

- **Purple**: Flags with an incorrectly flagged tile near

You can adjust the **check delay** in `config.env` to control how often the overlay updates.

### 2. Running the Bot

The bot automates gameplay by detecting the board state and clicking tiles accordingly.

    python bot.py

- Unlike the hint tool, the bot **scans the entire screen**.

- The bot will:
    1. Detect the Minesweeper grid and analyze the game state.
    
    2. Identify **safe moves** and flag **mines**.
    
    3. Click tiles **sequentially** in a logical order.
    
    4. Make **random choices when necessary**, as Minesweeper sometimes requires guessing.

The bot will **automatically stop** when it has no moves left after scanning the board twice, basically at the **end of the game**.

## Implementation Details

### 1. `common.py`

- **Purpose**: Provides essential utility functions for detecting, extracting, and processing Minesweeper grid from ascreenshot.

- **Technologies Used**:

    - **OpenCV**: Handles image processing tasks, such as color thresholding, contour detection, and tile classification.
    
    - **NumPy**: Used for array manipulation and efficient color filtering.

- **Key Features**:

    - Detects the Minesweeper playing field using color-based segmentation.
    
    - Extracts tile grid coordinates for further processing.
    
    - Classifies tiles based on their unique colors to interpret game state.
    
    - Implements a function to retrieve neighboring tiles for logical analysis.

### 2. `hint.py`

- **Purpose**: Analyzes Minesweeper tiles and their neighbors to generate visual overlay hint.

- **Technologies Used**:

    - **OpenCV**: Generates an overlay displaying hints on the game board.
    
    - **NumPy**: Performs efficient array-based operations for image manipulation.
    
    - **PyAutoGUI**: Captures screenshots for real-time game state analysis.
    
    - **Dotenv & OS**: Loads configuration settings from environment variables.

- **Key Features**:

    - Evaluates tile neighbors to mark safe moves and potential mines.
    
    - Detects and highlights incorrect flags.
    
    - Generates a transparent overlay displaying hints in a new window.
    
    - Runs continuously, updating hints in real time with adjustable delay.

### 3. `bot.py`

- **Purpose**: Automates playing Minesweeper by analyzing the game state, determining safe moves, and making clicks accordingly.

- **Technologies Used**:

    - **OpenCV**: Processes screenshots to identify game elements.
    
    - **NumPy**: Efficiently processes image data.
    
    - **PyAutoGUI**: Automates mouse clicks for interacting with the game.
    
    - **Dotenv & OS**: Loads configuration settings for customizable behavior.

- **Key Features**:

    - Identifies numbers, flags, and unknown tiles.
    
    - Clicks safe tiles, flags dangerous ones, and avoids uncertain ones unless necessary.
    
    - Enables rapid execution for faster gameplay by turning on turbo mode.

    - Uses hints to decide where to click next dynamically.

### 4. `calibration.py`

- **Purpose**: Helps calibrate the Minesweeper bot by adjusting tile and field padding values for accurate grid detection.

- **Key Features**:

    - Detects the minefield and extracts grid coordinates.
    
    - Displays an overlay of the detected grid.
    
    - Allows real-time adjustment of padding values using `W`, `A`, `S`, `D` keys.
    
    -Saves calibrated settings to `config.env` upon pressing `Enter`.