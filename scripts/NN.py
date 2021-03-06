#!/usr/bin/env python3

import numpy as np
import sys


class Loss:
    """
    Parent Class for Loss Functions
    """

    def loss(self, *args, **kwargs):
        """
        return child class loss function

        :param x: array-like
        :param y: array-like

        :returns: array-like
        """

        return self.__loss__(*args, **kwargs)

    def derivative(self, *args, **kwargs):
        """
        return derivative of child class loss function

        :param x: array-like
        :param y: array-like

        :returns: array-like
        """

        return self.__derivative__(*args, **kwargs)


class MSE(Loss):
    """
    Mean Squared Error Loss Function
    """

    def __loss__(self, x, y):
        """
        Calculates Mean Squared Error Loss Function
        """

        return np.mean((x - y)**2)

    def __derivative__(self, x, y):
        """
        Calculates Derivative of Mean Squared Error w.r.t to X
        """

        return 2*np.mean(x - y)


class CE(Loss):
    """
    Cross Entropy Loss with SoftMax included
    """

    def softmax(self, x):
        """
        calculates softmax of a given array
        """

        exps = np.exp(x - np.max(x))
        return exps / np.sum(exps)

    def __loss__(self, x, y):
        """
        Applies softmax to an array then calculates loss
        """

        p = self.softmax(x)
        loss = np.sum(-y * np.log(p))
        return loss

    def __derivative__(self, x, y):
        """
        Calculates derivative of Cross Entropy w.r.t X
        (SoftMax gradient included)
        """

        grad = self.softmax(x) - y
        return grad


class Activation:
    """
    Parent class for Activation Functions
    """

    def activation(self, *args, **kwargs):
        """
        Return activation function from child class

        :params x: a 1D array to apply function to

        :returns x: a 1D array after function application
        """

        return self.__activation__(*args, **kwargs)

    def derivative(self, *args, **kwargs):
        """
        Return derivative of activation function from child class

        :params x: a 1D array to calculate derivative of

        :returns x: a 1D array of derivatives
        """

        return self.__derivative__(*args, **kwargs)


class Sigmoid(Activation):
    """
    Sigmoidal Activation function
    """

    def __positive__(self, x):
        """
        calculates positive terms
        """

        return 1 / (1 + np.exp(-x))

    def __negative__(self, x):
        """
        calculates negative terms
        """

        exps = np.exp(x)
        return exps / (1 + exps)

    def __activation__(self, x):
        """
        calculates sigmoid function in a numerically stable way
        """

        mask_p = x >= 0
        mask_n = ~mask_p

        sig = np.zeros_like(x)
        if np.any(mask_p):
            sig[mask_p] = self.__positive__(x[mask_p])

        if np.any(mask_n):
            sig[mask_n] = self.__negative__(x[mask_n])

        return sig

    def __derivative__(self, x):
        """
        implemented derivative of sigmoid function
        """

        sig = self.__activation__(x)
        return sig * (1 - sig)


class TanH(Activation):
    """
    Tanh Activation Function
    """

    def __activation__(self, x):
        """
        calculates activation
        """

        ez = np.exp(x)
        enz = np.exp(-x)

        return (ez - enz) / (ez + enz)

    def __derivative__(self, x):
        """
        calculates derivative
        """

        tanh = self.__activation__(x)

        return 1 - (tanh**2)


class Free(Activation):
    """
    Empty Activation Layer
    """

    def __activation__(self, x):
        """
        pass current input forward without modification
        """
        return x

    def __derivative__(self, x):
        """
        pass constant derivative backwards
        """

        return 1


class NeuralNetwork:
    """
    Implementation of a feed forward neural network with backpropagation

    :param layers: a list of (int, NN.Activation) tuples to specify layers
    :param learning_rate: the learning rate to train model with
    """

    def __init__(self, layers, learning_rate=0.1):

        self.layers = np.array(layers)
        self.learning_rate = np.array(learning_rate).reshape(1, 1)

        self.params = {
            "weights": [],
            "f": [],
            "bias": [],
            "zs": [],
            "as": []
        }

        self.d_weights = []
        self.d_bias = []

        self._initialize_params()

    def _initialize_params(self):
        """
        randomly initializes weights and biases

        stores all internal parameters within indexable dictionary
        """

        for i in np.arange(self.layers.shape[0]):

            if i > 0:

                self.params['weights'].append(
                    np.random.random(
                        (self.layers[i][0], self.layers[i-1][0])
                    )
                )

                self.params['bias'].append(
                    np.random.random(self.layers[i][0])
                )

            self.params['zs'].append(
                np.zeros(self.layers[i][0]).reshape(self.layers[i][0], 1)
            )

            self.params['as'].append(
                np.zeros(self.layers[i][0]).reshape(self.layers[i][0], 1)
            )

            if self.layers[i][1] is None:
                self.params['f'].append(
                    self.layers[i][1]
                )

            else:
                self.params['f'].append(
                    self.layers[i][1]()
                )

    def forward(self, x):
        """
        forward propagation through network

        :params x: input layer to pass forward

        :returns y: final activation layer
        """

        self.params['as'][0] = x

        for idx in np.arange(1, self.layers.shape[0]):

            # index previous activations
            a = self.params['as'][idx-1]

            # index weights
            w = self.params['weights'][idx-1]

            # index bias
            b = self.params['bias'][idx-1]

            # calculate z_array
            self.params['zs'][idx] = (
                (a @ w.T) + b
            )

            # calculate activation
            self.params['as'][idx] = self.params['f'][idx].activation(
                self.params['zs'][idx]
            )

        return self.params['as'][-1]

    def backward(self, y, Loss):
        """
        calculates gradients via backpropagation

        :param y: true values to calculate loss
        :param Loss: NN.Loss object to calculate derivative with
        """

        # cache previous layers derivatives
        cache_dC_dA_dZ = []

        # initialize derivative weights and biases to fill
        d_weights = self.params['weights'].copy()
        d_bias = self.params['bias'].copy()

        # walk through network backwards
        for idx in np.arange(self.layers.shape[0])[::-1]:

            # dont derive the input layer
            if idx == 0:
                break

            # derivative of the cost function
            elif idx == self.layers.shape[0] - 1:

                # derivative of cost wrt final activation
                dC_dA = np.full(
                    self.layers[idx][0],
                    Loss.derivative(self.params['as'][idx], y)
                )
                dC_dA = dC_dA.reshape(1, dC_dA.size)

            # derivative of cost wrt layers activation
            else:

                # calculates current activation derivative using cached layers
                dC_dA = cache_dC_dA_dZ[-1].T @ self.params['weights'][idx]

            # derivative of activation wrt z-layer
            dA_dZ = self.params['f'][idx].derivative(
                self.params['as'][idx]
            )

            # derivative of z-layer wrt to weights
            dZ_dW = self.params['as'][idx-1].\
                reshape(1, self.params['as'][idx-1].size)

            # perform shared multiplicative term
            dC_dA_dZ = (dC_dA * dA_dZ).reshape(self.layers[idx][0], 1)

            # derivative of cost wrt to weights
            dC_dW = self.learning_rate * (dC_dA_dZ @ dZ_dW)

            # derivative of cost wrt to bias
            dC_dB = (self.learning_rate * dC_dA_dZ).reshape(-1)

            # cache calculated derivatives
            cache_dC_dA_dZ.append(dC_dA_dZ)
            d_weights[idx - 1] = dC_dW.copy()
            d_bias[idx - 1] = dC_dB.copy()

        self.d_weights.append(d_weights)
        self.d_bias.append(d_bias)

    def step(self):
        """
        Steps through weights and biases and applies derivatives
        """

        # iterate through layers
        for i in np.arange(len(self.params['weights'])):

            # prepare tensor
            d_weight_tensor = []
            d_bias_tensor = []

            # iterate through all derivatives
            for mdx in np.arange(len(self.d_weights)):

                dw = self.d_weights[mdx][i]
                db = self.d_bias[mdx][i]

                d_weight_tensor.append(dw)
                d_bias_tensor.append(db)

            # consolidate arrays into multidimensional tensor
            d_weight_tensor = np.array(d_weight_tensor)
            d_bias_tensor = np.array(d_bias_tensor)

            # take mean across the zero axis
            mean_d_weight_tensor = d_weight_tensor.mean(axis=0)
            mean_d_bias_tensor = d_bias_tensor.mean(axis=0)

            # update weights and biases
            self.params['weights'][i] -= mean_d_weight_tensor
            self.params['bias'][i] -= mean_d_bias_tensor

    def clear(self):
        """
        Empty the current derivatives and biases
        """

        self.d_weights = []
        self.d_bias = []

    def fit(self, X, Y, Loss, n_epochs=100, status_updates=10, verbose=False):
        """
        Trains model given X:observations and Y:labels

        :param X: observations to pass through network
        :param Y: labels to use in backpropagation
        :param Loss: NN.Loss object as Cost function
        :param n_epochs: Number of epochs to train model
        :param status_updates: Number of epochs to report mean loss
        :param verbose: Boolean of verbosity
        """

        # iterate through dataset
        for epoch in np.arange(n_epochs):

            # holds losses during epoch
            losses = []

            # iterate through observations and labels
            for x, y in zip(X, Y):

                # forward pass
                pred = self.forward(x)

                # calculate loss
                loss = Loss.loss(pred, y)

                # calculate gradient
                self.backward(y, Loss)

                # store loss
                losses.append(loss)

            # applies gradient descent
            self.step()

            # clears gradients between epochs
            self.clear()

            # prints out current epochs mean loss
            if verbose:
                if (epoch % status_updates == 0) | (epoch == n_epochs-1):
                    print(
                        "Mean Loss at epoch {} : {:.6f}".format(
                            epoch, np.mean(losses)
                            ),
                        file=sys.stderr
                    )

    def minibatch_reader(self, *args, batch_size=10):
        """
        Shuffles indices and yields batches of indices

        :params args: any number of datasets to create batched indices for
        :returns g: a generator of indices used to subset datasets
        """

        num_obs = np.unique([a.shape[0] for a in args])
        assert num_obs.size == 1

        random_indices = np.random.choice(
            num_obs[0], size=num_obs[0], replace=False
        )

        it = 0
        while True:
            i = batch_size * it
            j = i + batch_size
            it += 1

            if i >= num_obs[0]:
                break

            if j > num_obs[0]:
                j = num_obs[0]

            yield random_indices[i:j]

    def minibatch_fit(self, X, Y, Loss, n_epochs=100,
                      batch_size=10, status_updates=10,
                      verbose=False
                      ):
        """
        Trains a model with minibatch regularization

        :param X: observations to pass through network
        :param Y: labels to use in backpropagation
        :param Loss: NN.Loss object as Cost function
        :param n_epochs: Number of epochs to train model
        :param batch_size: Number of observations in each batch
        :param status_updates: Number of epochs to report mean loss
        :param verbose: Boolean of verbosity
        """

        # iterate through dataset
        for epoch in np.arange(n_epochs):

            # stores losses
            losses = []

            # read indices from minibatches
            for ind in self.minibatch_reader(X, Y, batch_size=batch_size):

                # subset x and y with indices
                sub_X = X[ind]
                sub_Y = Y[ind]

                # fit batch
                for x, y in zip(sub_X, sub_Y):

                    # forward pass
                    pred = self.forward(x)
                    loss = Loss.loss(pred, y)

                    # backward prop
                    self.backward(y, Loss)
                    losses.append(loss)

                # apply gradients each batch
                self.step()
                self.clear()

            if verbose:
                if (epoch % status_updates == 0) | (epoch == n_epochs-1):
                    print(
                        "Mean Loss at epoch {} : {:.6f}".format(
                            epoch, np.mean(losses)
                            ),
                        file=sys.stderr
                    )

    def predict(self, X):
        """
        Feeds forward all observations in X and returns predictions

        :param X: Observations to predict values for
        :returns Y: Predicted labels of X
        """

        # stores predictions
        predictions = []
        for x in X:

            # forward pass
            pred = self.forward(x)
            predictions.append(pred)

        return np.array(predictions)
