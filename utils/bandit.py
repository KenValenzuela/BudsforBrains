import numpy as np

class LinUCB:
    def __init__(self, n_arms: int, dim: int, alpha: float = 0.3):
        self.n_arms, self.dim, self.alpha = n_arms, dim, alpha
        self.A = [np.eye(dim) for _ in range(n_arms)]   # d×d
        self.b = [np.zeros((dim, 1)) for _ in range(n_arms)]

    # private helper
    def _theta(self, arm: int) -> np.ndarray:
        return np.linalg.solve(self.A[arm], self.b[arm])

    def score(self, contexts: np.ndarray) -> np.ndarray:
        """Return UCB scores for each arm (ctxs shape = (n_arms, dim))."""
        s = []
        for a in range(self.n_arms):
            x = contexts[a].reshape(-1, 1)
            theta = self._theta(a)
            mean = float(theta.T @ x)
            var  = float(x.T @ np.linalg.inv(self.A[a]) @ x)
            s.append(mean + self.alpha * np.sqrt(var))
        return np.array(s)

    def update(self, arm: int, reward: float, context: np.ndarray):
        x = context.reshape(-1, 1)
        self.A[arm] += x @ x.T
        self.b[arm] += reward * x
