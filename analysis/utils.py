

def prob_not(x):    return 1.0 - x
def prob_and(x, y): return x*y
def prob_or(x, y):  return (x + y) - x*y


def prob_trials(initial_prob, trials):
    current_prob = initial_prob
    for _ in range(trials):
        current_prob = prob_or(current_prob, initial_prob)
    return current_prob