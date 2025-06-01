class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimated_error, initial_value):
        self.process_variance = process_variance  # Process noise
        self.measurement_variance = measurement_variance  # Measurement noise
        self.estimated_error = estimated_error  # Estimation error
        self.posteri_estimate = initial_value  # Last estimated value

    def update(self, measurement):
        # Prediction Update
        self.estimated_error += self.process_variance

        # Measurement Update
        kalman_gain = self.estimated_error / (self.estimated_error + self.measurement_variance)
        self.posteri_estimate = self.posteri_estimate + kalman_gain * (measurement - self.posteri_estimate)
        self.estimated_error = (1 - kalman_gain) * self.estimated_error

        return self.posteri_estimate

