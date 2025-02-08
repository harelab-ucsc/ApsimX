"""Tools for working with apsim meterological files suffixed with .met"""

from datetime import datetime, timedelta


class MetGenerator:
    def __init__(
        self,
        start: datetime,
        end: datetime,
        site: str,
        lat: float,
        lon: float,
        tav: float = 20,
        amp: float = 0,
    ):
        """Default constructor

        Temperature amplitude is the difference between max and min temperature
        throughout all the weather data

        Args:
            start: Start date
            end: End date
            site: Site name
            lat: Latitude
            lon: Longitude
            tav: Average temperature
            amp: Temperature amplitude
        """

        self.start = start
        self.end = end
        self.site = site
        self.lat = lat
        self.lon = lon
        self.tav = tav
        self.amp = amp

        # default solar radiation
        self.rad = 10

    def save(self, file: str, overwrite: bool = True):
        """Saves output to file

        Args:
            file: Path to met file
            overwrite: Allow file overwriting
        """

        if overwrite:
            mode = "w"
        else:
            mode = "x"

        with open(file, mode, encoding="utf-8") as f:
            self.write_header(f)
            self.write_data(f)

    def write_header(self, f):
        """Writes a header to an open file"""

        f.write("!empty met file\n")
        self.write_kv(f, "site", self.site)
        self.write_kv(f, "latitude", self.lat)
        self.write_kv(f, "longitude", self.lon)
        self.write_kv(f, "tav", self.tav)
        self.write_kv(f, "amp", self.amp)

    def write_kv(self, f, key: str, value):
        """Write key value pairs to file

        Writes in the format "{key} = {value}"

        Args:
            key: Key
            value: Value
        """

        f.write(f"{key} = {value}\n")

    def write_data(self, f):
        """Write data and column headers to an open file

        Args:
            f: Open file
        """

        f.write("year day radn maxt mint rain rh windspeed\n")
        f.write("() () (MJ/m2/day) (oC) (oC) (mm) (%) (m/s)\n")

        cur = self.start
        while cur <= self.end:
            year = cur.year
            day = cur.strftime("%j")
            temp = self.tav
            rad = self.rad
            f.write(f"{year} {day} {rad} {temp} {temp} 0 0 0\n")
            # add a day to the current date
            cur += timedelta(1)
