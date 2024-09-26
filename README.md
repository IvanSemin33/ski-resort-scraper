# Ski Resort Scraper

A Python-based web scraper that collects data about ski resorts from the Ski Resort Info website. The scraper retrieves various statistics, including resort names, logos, websites, trail maps, altitude, slope statistics, lift statistics, and ticket prices. The collected data is saved in an Excel file for easy access and analysis.

## Features

- Scrapes detailed information about ski resorts.
- Extracts and organizes data into a structured format.
- Saves the scraped data into an Excel file.
- Handles interruptions gracefully, saving data before exit.

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - beautifulsoup4
  - pandas
  - colorama

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SkiresortScraper.git
   cd SkiresortScraper
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the scraper:
   ```bash
   python SkiresortScraper.py
   ```

2. The scraper will start collecting data from the Ski Resort Info website. It will print the progress in the terminal and save the results to an Excel file named `skiResort.xlsx` in the project directory.

3. To stop the scraper at any time, use `Ctrl + C`. The scraper will save the collected data before exiting.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add some feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the developers of the libraries used in this project: [Requests](https://docs.python-requests.org/en/master/), [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), and [Pandas](https://pandas.pydata.org/).
- Special thanks to [Beau Bellamy](https://github.com/beaubellamy) for the original repository that inspired this project.