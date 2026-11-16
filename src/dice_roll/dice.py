import numpy as np
import datetime as dat
from pathlib import Path

class Dice():
    def __init__(self, seed):
        self.seed = seed
        self.rng = np.random.default_rng(seed=seed)
        self.dice = [4, 6, 8, 10, 12, 20]
        self.log = ""
        self.iroll = 0
        self.now = None
        self.n = [None]*6

    def _dx(self, d=6, x=1):
        return self.rng.integers(1, d+1, x)

    def roll(self, number):
        self.iroll += 1
        self.now = dat.datetime.now()
        for i,j in enumerate(self.dice):
            self.n[i] = self._dx(d=j, x=number[i])

        self.save_roll()
        return (self.now, self.n)

    def save_roll(self):
        datetime_string = self._format_datetime(self.now)
        self.log += f"Roll {self.iroll}  {datetime_string}\n"
        count_width = len(str(max(len(result) for result in self.n)))
        for d, result in zip(self.dice, self.n):
            self.log += f"d{d:<2}  ({len(result):>{count_width}} dice)  =  {result}\n"
        self.log += "\n"

    def save_log(self):
        datetime_string = self._format_datetime(dat.datetime.now())
        log_dir = Path.cwd() / "dice_roll_logs"
        log_dir.mkdir(exist_ok=True)
        filename = log_dir / f"log_{datetime_string}.txt"
        with open(filename, "x", encoding="utf-8") as file:
            file.write(self.log)
        return filename

    @staticmethod
    def _format_datetime(dt):
        return dt.strftime("%Y_%m_%d_%H_%M_%S_%f")

if __name__ == "__main__":
    n = Dice(seed=1024)
    print(n._dx(d=4, x=3))

    n = Dice(seed=None)
    print(n._dx(d=20, x=10))

    out = n.roll([1,1,1,1,1,10])
    out = n.roll([1,20,1,10,1,10])

    print(n.log)
    n.save_log()
    