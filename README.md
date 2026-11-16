# Dice Roll

A lightweight desktop application for rolling polyhedral dice, built with Python and PySide6.

## Features

- Support for six types of dice: d4, d6, d8, d10, d12, and d20.
- Roll multiple dice of different types simultaneously.
- Scalable SVG dice graphics with dynamically displayed values.
- Adaptive graphical display with randomized dice positions.
- Scrollable roll area for large numbers of dice.
- Timestamped roll history.
- Export of cumulative roll history to text files.

## Requirements

- Python 3.10 or later
- NumPy
- PySide6

## Installation

Clone the repository and navigate to the project directory. Install the application and its dependencies:

```bash
python -m pip install .
```

For uninstallation

```bash
python -m pip uninstall dice_roll
```

## Usage

Launch the application using:

```bash
python -m dice_roll
```

Alternatively, use the installed application command:

```bash
dice_roll
```

Select the number of dice of each type and click **Roll**. The results are displayed graphically in the central area, and the roll history is recorded in the right panel.

Click **Save** to export the current roll history.

## Roll History

Log files are saved in a `dice_roll_logs/` directory, automatically created in the current working directory when you save a log.

Each file contains the complete roll history of the current session. Filenames include timestamps with microsecond precision, and existing files are never overwritten.

Saving the log does not reset the roll history.

The dice-rolling backend is independent of the graphical interface, allowing it to be used as a standalone Python module.

