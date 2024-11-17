# DLIB with CUDA Installation

1. Download [Visual Studio 2022 Community](https://visualstudio.microsoft.com/downloads/), install necessary individual components comprise of:
    - MSVC build tools
    - C++ CMake tools
    - Windows 10/11 SDK
    
2. Download and install [CUDA](https://developer.nvidia.com/cuda-downloads) and [cuDNN](https://developer.nvidia.com/cudnn-downloads?target_os=Windows&target_arch=x86_64) (Tarball version). To integrate both of them, extract the downloaded cuDNN zip, copy files in each folder and paste in corresponding CUDA folder. For example:
    ```
    From the extracted cudnn/bin folder, copy to C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5\bin
    and so on...
    ```

3. Go to your project folder where dlib with CUDA support will be installed, run these commands in the terminal:
    ```
    git clone https://github.com/davisking/dlib.git
    cd dlib
    mkdir build
    cd build

    cmake .. -DDLIB_USE_CUDA=1 -DUSE_AVX_INSTRUCTIONS=1
    or alternatively
    cmake -G "Visual Studio 17 2022" -A x64 -DDLIB_USE_CUDA=1 -DUSE_AVX_INSTRUCTIONS=1 ..

    cmake --build .
    cd ../dlib/python_examples
    python setup.py install
    ```