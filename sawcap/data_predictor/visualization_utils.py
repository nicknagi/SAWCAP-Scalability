import matplotlib.pyplot as plt

def plot_continuation(data, start2, metadata, labels):
    """ Plots the curves for a model run, given the arrays loss, iou, accuracy arrays and 		corresponsding metadata

    Args:
        loss: array of losses, where n - number of curves to compare (usually train vs 			validation) and i - number of iterations for the plot

	metadata: What kind of data is present (usually train, validation)

    """
    title = ""
    n = len(data[0]) # number of epochs
    title = metadata[0] + " vs " + metadata[1] + " "+ labels[1] + " per " + labels[0]
    plt.title(title)

    plt.plot(range(1,n+1), data[0], label=metadata[0])
    plt.plot(range(start2,n+1), data[1][start2-1:], label=metadata[1])

    plt.xlabel(labels[0])
    plt.ylabel(labels[1])
    plt.legend(loc='best')
    plt.show()

def plot_a_curve(data, metadata, labels):
  """ Plots the curves for a model run, given the arrays loss, iou, accuracy arrays and 		corresponsding metadata

  Args:
      loss: array of losses, where n - number of curves to compare (usually train vs 			validation) and i - number of iterations for the plot

  metadata: What kind of data is present (usually train, validation)

  """
  title = ""
  n = len(data[0]) # number of epochs
  for i in range(len(metadata)):
    if i != 0:
      title += " vs "
    title += metadata[i]
    plt.plot(range(1,n+1), data[i], label=metadata[i])
  title = title + " " + labels[1] + " per " + labels[0]
  plt.title(title)
  plt.xlabel(labels[0])
  plt.ylabel(labels[1])
  plt.legend(loc='best')
  plt.show()