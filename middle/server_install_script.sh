sudo pip install tensorflow tensorflow-serving-api redis Flask nltk
sudo apt-get install sqlite3

# redis install
wget http://download.redis.io/redis-stable.tar.gz && tar xvzf redis-stable.tar.gz
cd redis-stable && make & make test
## if test pass, ignore the latter
## <ignore>
wget http://downloads.sourceforge.net/tcl/tcl8.6.1-src.tar.gz
sudo tar xzvf tcl8.6.1-src.tar.gz  -C /usr/local/
cd  /usr/local/tcl8.6.1/unix/ && sudo ./configure
sudo make && sudo make install 
## </ignore>
sudo cp src/redis-server /usr/local/bin/ && sudo cp src/redis-cli /usr/local/bin/

git clone https://github.com/Luke-WENG/efficient_nmt_serving.git

# Flask
cd efficient_nmt_serving/middle/flaskr && sqlite3 database/flaskr.db < schema.sql
# python
# # <python>
# from flaskr import init_db
# init_db()
# # </python>

# Redis Start
screen
redis-server

# # Open NMT
# git clone https://github.com/OpenNMT/OpenNMT-tf.git
# cd OpenNMT-tf && git checkout v1.0.0

# TensorFlow Serving
echo "deb [arch=amd64] http://storage.googleapis.com/tensorflow-serving-apt stable tensorflow-model-server tensorflow-model-server-universal" | sudo tee /etc/apt/sources.list.d/tensorflow-serving.list
curl https://storage.googleapis.com/tensorflow-serving-apt/tensorflow-serving.release.pub.gpg | sudo apt-key add -
sudo apt-get update && sudo apt-get install tensorflow-model-server


# Model download
mkdir ~/model && cd ~/model
wget https://s3.amazonaws.com/opennmt-models/averaged-ende-export500k.tar.gz
tar xvzf averaged-ende-export500k.tar.gz
mkdir 1 && mv averaged-ende-export500k/* 1/ && mv 1 averaged-ende-export500k/

# if running tensorflow without certain lib:
# libstdc++.so.6: version `CXXABI_1.3.11' not found `
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update && sudo apt -y install gcc-6 g++-6
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-6 60 --slave /usr/bin/g++ g++ /usr/bin/g++-6    


cd ~
tensorflow_model_server --port=9000 --model_name=aver_ende --model_base_path=$HOME/model/averaged-ende-export500k

# test
python ~/efficient_nmt_serving/client/nmt_client.py --model_name aver_ende --host=localhost --port=9000 --timeout=3600

# Run



# TensorFlow Serving with GPU
## Install Bazel
sudo apt-get update && sudo apt-get install -y openjdk-8-jdk
echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add -
sudo apt-get update && sudo apt-get install -y bazel && sudo apt-get upgrade -y bazel

sudo apt-get update && sudo apt-get install -y \
        build-essential \
        curl \
        libcurl3-dev \
        git \
        libfreetype6-dev \
        libpng12-dev \
        libzmq3-dev \
        pkg-config \
        python-dev \
        python-numpy \
        python-pip \
        software-properties-common \
        swig \
        zip \
        zlib1g-dev \
        screen \
        redis-tools \
        # to compile clipper
        libboost-all-dev \
        libzmq3-dev \
        cuda-command-line-tools \
        sqlite3

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/extras/CUPTI/lib64

sudo pip2 install --upgrade pip

## Pip Install packages
sudo pip2 install tensorflow-gpu \
        tensorflow-serving-api \
        scikit-learn \
        scipy \
        requests \
        psutil \
        pandas \
        matplotlib \
        seaborn \
        redis \
        grpcio \
        nltk \
        Flask

# # Install TensorFlow from Source
cd $HOME
git clone --recurse-submodules https://github.com/tensorflow/serving
cd serving

bazel build -c opt --config=cuda --verbose_failures tensorflow_serving/model_servers:tensorflow_model_server
# --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-mfpmath=both --copt=-msse4.2 -k --jobs 6 

cd $HOME/serving
bazel-bin/tensorflow_serving/model_servers/tensorflow_model_server --port=9000 --model_name=mnist --model_base_path=/tmp/mnist_model/