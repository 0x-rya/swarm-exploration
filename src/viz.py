import matplotlib.pyplot as plt

# read from valkey
# draw a grid with different colors
def plot_grid(data, saveImageName):
    fig, ax = plt.subplots()
    ax.imshow(data, cmap=cmap, norm=norm)
    # draw gridlines
    ax.grid(which='major', axis='both', linestyle='-', color='k', linewidth=1)

    ax.set_xticks(np.arange(0.5, rows, 1));
    ax.set_yticks(np.arange(0.5, cols, 1));
    plt.tick_params(axis='both', which='both', bottom=False,   
                    left=False, labelbottom=False, labelleft=False) 
    fig.set_size_inches((8.5, 11), forward=False)
    plt.savefig(saveImageName + ".png", dpi=500)