# A simple linear neural network implementation in Tensorflow
# Trained on the sample datasets
import tensorflow as tf
import dutils.debug as dbg
from numpy import array as narray

class NeuralNetwork():
    def __init__(self, il_nn, hl_nn, ol_nn, lr=0.1, ns=500, bs=5, ds=50):
        # Making Python type-safe!
        if not isinstance(lr, int) and not isinstance(lr, float):
            raise Exception("Learning rate must be an integer or float.")
        if not isinstance(ns, int):
            raise Exception("Number of steps must be an integer.")
        if not isinstance(bs, int):
            raise Exception("Batch size must be an integer.")
        if not isinstance(il_nn, int):
            raise Exception("Input layer number of neurons must be an integer.")
        if not isinstance(ol_nn, int):
            raise Exception("Output layer number of neurons must be an integer.\
            ")
        if not isinstance(hl_nn, list):
            e_msg = "Hidden layer number of neurons must be a a list of\
                integers."
            raise Exception(e_msg)
            for i in hl_nn:
                if not isinstance(i, int):
                    raise Exception(e_msg)
        self.learning_rate = lr
        self.number_steps = ns
        self.batch_size = bs
        self.display_step = ds
        self.input_layer_number_neurons = il_nn
        self.output_layer_number_neurons = ol_nn
        self.hidden_layer_number_neurons = hl_nn
        self.data_point_size = self.input_layer_number_neurons +\
            self.output_layer_number_neurons
        self.train_data = []
        self.test_data = []
        self.weights = []
        self.bias = []
        self.tf_weights = None
        self.tf_bias = []
        self.tf_init = None
        self.tf_layers = None
        self.x_vector = None
        self.y_vector = None

    def init_network(self):
        self.x_vector = tf.placeholder("float",\
            [None, self.input_layer_number_neurons])
        self.y_vector = tf.placeholder("float",\
            [None, self.output_layer_number_neurons])

        # Initialize weight variables
        self.tf_weights = {}
        for i in range(len(self.hidden_layer_number_neurons)):
            if i == 0:
                self.tf_weights["h" + str(i+1)] = tf.Variable(\
                    tf.random_normal([self.input_layer_number_neurons,\
                    self.hidden_layer_number_neurons[i]]), name="h" + str(i+1))
                self.weights.append(\
                    [self.input_layer_number_neurons * [0]] *\
                    self.hidden_layer_number_neurons[i])
            else:
                self.tf_weights["h" + str(i+1)] = tf.Variable(\
                    tf.random_normal([self.hidden_layer_number_neurons[i-1],\
                    self.hidden_layer_number_neurons[i]]), name="h" + str(i+1))
                self.weights.append(\
                    [self.hidden_layer_number_neurons[i-1] * [0]] *\
                    self.hidden_layer_number_neurons[i]
                )

        # Output weights
        if len(self.hidden_layer_number_neurons) == 0:
            self.tf_weights["out"] = tf.Variable(tf.random_normal([\
                self.input_layer_number_neurons,\
                self.output_layer_number_neurons]), name="out")
            self.weights.append(\
                [self.input_layer_number_neurons * [0]] *\
                self.output_layer_number_neurons)
        else:
            self.tf_weights["out"] = tf.Variable(tf.random_normal([\
                self.hidden_layer_number_neurons[-1],
                self.output_layer_number_neurons]), name="out")
            self.weights.append(\
                [self.hidden_layer_number_neurons[-1] * [0]] *\
                self.output_layer_number_neurons)

        # Bias
        self.tf_bias = {}
        for i in range(len(self.hidden_layer_number_neurons)):
            self.tf_bias["b" + str(i+1)] = tf.Variable(tf.random_normal([\
                self.hidden_layer_number_neurons[i]]), name="b" + str(i+1))
            self.bias.append(self.hidden_layer_number_neurons[i] * [0])

        # Output bias
        self.tf_bias["out"] = tf.Variable(tf.random_normal(\
            [self.output_layer_number_neurons]), name="b" + str(i+1))
        self.bias.append(self.output_layer_number_neurons * [0])

        # Initialize layers
        self.tf_layers = {}
        for i in range(len(self.hidden_layer_number_neurons)):
            if i == 0:
                self.tf_layers["l" + str(i+1)] = tf.add(tf.matmul(\
                    self.x_vector, self.tf_weights["h" + str(i+1)]),\
                    self.tf_bias["b" + str(i+1)])
            else:
                self.tf_layers["l" + str(i+1)] = tf.add(tf.matmul(\
                    self.tf_layers["l" + str(i)],\
                    self.tf_weights["h" + str(i+1)]),\
                    self.tf_bias["b" + str(i+1)])

        if len(self.hidden_layer_number_neurons) == 0:
            self.tf_layers["out"] = tf.matmul(
                self.x_vector, self.tf_weights["out"]) + self.tf_bias["out"]
        else:
            # Using the previous layer doesn't work. Need to create an
            # equivalent placeholder instead
            self.tf_layers["out"] = tf.matmul(\
                self.tf_layers["l" +\
                str(len(self.hidden_layer_number_neurons))],\
                self.tf_weights["out"]) + self.tf_bias["out"]
        # Construct model
        logits = self.tf_layers["out"]
        prediction = tf.nn.relu(logits)

        # Loss and optimizer
        self.loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
            logits=logits, labels=self.y_vector))
        optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        self.train_op = optimizer.minimize(self.loss_op)

        # Model evaluation
        compare_pred = tf.equal(tf.argmax(prediction, 1),\
            tf.argmax(self.y_vector, 1))
        self.accuracy = tf.reduce_mean(tf.cast(compare_pred, tf.float32))

        # Initialize tf variables
        self.tf_init = tf.global_variables_initializer()

    def train(self):
        with tf.Session() as sess:
            sess.run(self.tf_init)
            for step in range(1, self.number_steps+1):
                start = ((step-1) * self.batch_size) % len(self.train_data)
                end = (step * self.batch_size) % len(self.train_data)
                # For being to slide over dataset in a batch window
                if end == 0:
                    end = None
                x_train_vector = list(map(lambda x: list(x[:self.input_layer_number_neurons]),\
                    self.train_data[start:end]))
                y_train_vector = list(map(lambda x: list(x[self.input_layer_number_neurons:]),\
                    self.train_data[start:end]))
                # Backpropogation
                sess.run(self.train_op,
                    feed_dict={self.x_vector: x_train_vector, self.y_vector: y_train_vector})
                if step % self.display_step == 0 or step == 1:
                    # Calculate loss and accuracy
                    loss, acc = sess.run([self.loss_op, self.accuracy],\
                        feed_dict={self.x_vector: x_train_vector, self.y_vector: y_train_vector})
                    dbg.dprint("Step " + str(step) + ", Loss= " + \
                          "{:.4f}".format(loss) + ", Training Accuracy= " + \
                          "{:.3f}".format(acc))

            dbg.dprint("Training Finished!")

            if (len(self.test_data) != 0):
                # Only get testing accuracy if both are provided before training
                x_test_vector = list(map(lambda x: list(x[:self.input_layer_number_neurons]),\
                    self.test_data))
                y_test_vector = list(map(lambda x: list(x[self.input_layer_number_neurons:]),\
                    self.test_data))
                # Get accuracy with test dataset
                dbg.dprint("Testing Accuracy:" +\
                    str(sess.run(self.accuracy,\
                        feed_dict={self.x_vector: x_test_vector, self.y_vector: y_test_vector})))

            dbg.dprint("Saving weights...")
            # Save the weights
            for l_i in range(len(self.hidden_layer_number_neurons)):
                for l_ni in range(len(self.weights[l_i])):
                    for pl_ni in range(len(self.weights[l_i][l_ni])):
                        self.weights[l_i][l_ni][pl_ni] = self.tf_weights["h" + str(l_i+1)][pl_ni][l_ni].eval()
                        # For last layer
                        if l_i == len(self.hidden_layer_number_neurons)-1:
                            self.weights[l_i][l_ni][pl_ni] = self.tf_weights["out"][pl_ni][l_ni].eval()
                        # For hidden layers
                        else:
                            self.weights[l_i][l_ni][pl_ni] = self.tf_weights["h" + str(l_i+1)][pl_ni][l_ni].eval()
            dbg.dprint("Weights saved!")

    def test(self):
        with tf.Session() as sess:
            sess.run(self.tf_init)
            if (len(self.test_data) != 0):
                # Only get testing accuracy if both are provided before training
                x_test_vector = list(map(lambda x: list(x[:self.input_layer_number_neurons]),\
                    self.test_data))
                y_test_vector = list(map(lambda x: list(x[self.input_layer_number_neurons:]),\
                    self.test_data))
                # Get accuracy with test dataset
                dbg.dprint("Testing Accuracy:" +\
                    str(sess.run(self.accuracy,\
                        feed_dict={self.x_vector: x_test_vector, self.y_vector: y_test_vector})))
            else:
                raise Exception("Please provide testing data before running the test method.")
    def load_train_data(self, train_data):
        # Validate dataset dimensions
        if(len(train_data[0]) == self.data_point_size):
            for data_point in train_data:
                assert(len(data_point) == self.data_point_size)
            self.train_data = narray(train_data)
        else:
            # Extra step for converting binary data into one-hot encoding for tf
            for data_point in train_data:
                assert(len(data_point) == (self.data_point_size-1))
            self.train_data = narray(self.binary_2_one_hot(train_data))

    def load_test_data(self, test_data):
        # Validate dataset dimensions
        if(len(test_data[0]) == self.data_point_size):
            for data_point in test_data:
                assert(len(data_point) == self.data_point_size)
            self.test_data = narray(test_data)
        else:
            # Extra step for converting binary data into one-hot encoding for tf
            for data_point in test_data:
                assert(len(data_point) == (self.data_point_size-1))
            self.test_data = narray(self.binary_2_one_hot(test_data))

    def binary_2_one_hot(self, data):
        # Convert binary class data for one-hot training
        # TODO: Make this work for higher-dimension data
        rVal = []
        for data_point in data:
            new_dp = []
            input_data = data_point[:self.input_layer_number_neurons]
            output_class = data_point[self.input_layer_number_neurons:][0]
            if output_class == 0:
                output_data = [1,0]
            elif output_class == 1:
                output_data = [0,1]
            else:
                raise Exception("Data should only have 2 classes.")
            new_dp.extend(input_data)
            new_dp.extend(output_data)
            rVal.append(tuple(new_dp))
        return rVal

    def load_dataset(self, dataset_obj):
        # Load training and testing data from dataset object
        if(len(dataset_obj.train_data[0]) == self.data_point_size):
            # Validate dataset dimensions
            for data_point in dataset_obj.train_data:
                    assert(len(data_point) == self.data_point_size)
            for data_point in dataset_obj.test_data:
                    assert(len(data_point) == self.data_point_size)
            # Load dataset
            self.train_data = narray(dataset_obj.train_data)
            self.test_data = narray(dataset_obj.test_data)
        else:
            # Extra step for converting binary data into one-hot encoding for tf
            for data_point in dataset_obj.train_data:
                    assert(len(data_point) == (self.data_point_size-1))
            for data_point in dataset_obj.test_data:
                    assert(len(data_point) == (self.data_point_size-1))
            # Load dataset
            self.train_data = narray(self.binary_2_one_hot(dataset_obj.train_data))
            self.test_data = narray(self.binary_2_one_hot(dataset_obj.test_data))

    def pack_weights(self):
        # TODO: Weights should be serialized into a 1-dimension narray in the
        # format defined in the danku contract
        return

    def unpack_weights(self):
        # TODO: Weights should be serialized into a 3-dimension narray in the
        # format defined in the danku contract
        return
