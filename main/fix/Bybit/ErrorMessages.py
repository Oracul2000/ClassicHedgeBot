import json
import time


class Error:
    route = 'main/tgmsgs/'

    def __init__(self, uid, etype, params) -> None:
        self.message = {
            "Type": etype,
            "User Id": uid
        }.update(params)

    def publish(self):
        t = time.time()
        with open(self.route + str(t), "w") as fp:
            json.dump(self.message, fp)


class TPError(Error):
    def __init__(self, uid, params) -> None:
        super().__init__(uid, 'Take Profit', params)


class PnLSizeError(Error):
    def __init__(self, uid, params) -> None:
        super().__init__(uid, 'PnL Size', params)


class NoInternetError(Error):
    def __init__(self, uid, params) -> None:
        super().__init__(uid, "No Internet", params)


class PositionInfo(Error):
    def __init__(self, uid, params) -> None:
        super().__init__(uid, "Position Information", params)


class MaxLossError(Error):
    def __init__(self, uid, params):
        print(
            f'MaxLossError2\nMaxLossError2\nMaxLossError2\n{params}\nMaxLossError2\nMaxLossError2\nMaxLossError2\n')
        super().__init__(uid, 'Max Loss', params)
        print('class MaxLossError(Error):', self.message)
