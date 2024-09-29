class PlotData:
    def __init__(self, x_values, y_values, labels=None):
        assert(labels is None or (len(labels) == len(y_values)))
        assert(all([len(x_values) == len(yv) for yv in y_values]))
        self.num_frames = len(x_values)
        self.num_plots = len(y_values)
        self.x_values = x_values
        self.y_values = y_values
        self.labels = labels
        

def get_plot_data_from_summary(summary):
        x = list([1,2,3,4,5])
        labels = []
        y = []
        for f in x:
            y.append(f*f)
        labels = ["vals"]
        return PlotData(x, [y], labels)