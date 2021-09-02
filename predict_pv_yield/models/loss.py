import math
import torch


class WeightedLosses:
    def __init__(self, decay_rate: int = None, forecast_length: int = 6):
        """
        Want to set up the MSE loss function so the weights only have to be calculated once.

        The weights exponentially decay depending on the 'decay_rate'.
        The forecast lentgh is needed to make sure the weights sum to 1
        """
        self.decay_rate = decay_rate
        self.forecast_length = forecast_length

        if self.decay_rate is None:
            self.decay_rate = math.log(2)

        # make weights from decay rate
        weights = torch.FloatTensor([math.exp(-self.decay_rate * i) for i in range(0, self.forecast_length)])

        # normalized the weights
        self.weights = weights / weights.sum()

    def get_mse_exp(self, output, target):
        return torch.sum(self.weights * (output - target) ** 2)

    def get_mae_exp(self, output, target):
        return torch.sum(self.weights * torch.abs(output - target))
