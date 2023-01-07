from datetime import datetime

from imp.data.colors import Colors


class BetterLogger:
    def log(self, agent: str, message: str, color: str = Colors.GREEN):
        print(
            "%s%s[%s%s%s%s%s]%s %s[%s%s%s%s@%s%s%s%s]%s ~ %s%s%s" % (
                Colors.E, Colors.BOLD, Colors.E, Colors.B, datetime.now(), Colors.E, Colors.BOLD, Colors.E,
                Colors.BOLD, Colors.E, Colors.C, agent, Colors.E, Colors.C, self.__class__.__name__, Colors.E,
                Colors.BOLD, Colors.E, color, message, Colors.E
            )
        )
