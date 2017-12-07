import mxnet as mx
from mxnet.test_utils import check_speed


def benchmark_convolution(data_shape, kernel, num_filter, pad, stride, no_bias=True, layout='NCHW', repeats=20):
    ctx_gpu = mx.gpu(0)
    data = mx.sym.Variable(name="data", shape=data_shape)
    # conv cudnn
    conv_cudnn = mx.sym.Convolution(data=data, kernel=kernel, num_filter=num_filter, pad=pad, stride=stride,
                                    no_bias=no_bias, layout=layout, cudnn_off=False, name="conv_cudnn")
    arg_shapes, _, _ = conv_cudnn.infer_shape(data=data_shape)
    input_data = mx.nd.random.normal(0, 0.2, shape=data_shape, ctx=ctx_gpu)
    conv_weight_name = conv_cudnn.list_arguments()[1]
    args = {data.name: input_data, conv_weight_name: mx.random.normal(0, 1, shape=arg_shapes[1], ctx=ctx_gpu)}
    conv_cudnn_time = check_speed(sym=conv_cudnn, location=args, ctx=ctx_gpu, N=repeats,
                                  grad_req='null', typ='forward') * 1000

    # quantized_conv2d
    qdata = mx.sym.Variable(name='qdata', shape=data_shape, dtype='int8')
    weight = mx.sym.Variable(name='weight', shape=arg_shapes[1], dtype='int8')
    min_data = mx.sym.Variable(name='min_data', shape=(1,), dtype='float32')
    max_data = mx.sym.Variable(name='max_data', shape=(1,), dtype='float32')
    min_weight = mx.sym.Variable(name='min_weight', shape=(1,), dtype='float32')
    max_weight = mx.sym.Variable(name='max_weight', shape=(1,), dtype='float32')
    quantized_conv2d = mx.sym.quantized_conv2d(data=qdata, weight=weight, min_data=min_data, max_data=max_data,
                                               min_weight=min_weight, max_weight=max_weight,
                                               kernel=kernel, num_filter=num_filter, pad=pad, stride=stride,
                                               no_bias=no_bias, layout=layout, cudnn_off=False, name='quantized_conv2d')
    qargs = {qdata.name: mx.quantization.quantize(input_data)[0],
             min_data.name: mx.quantization.quantize(input_data)[1],
             max_data.name: mx.quantization.quantize(input_data)[2],
             weight.name: mx.quantization.quantize(args[conv_weight_name])[0],
             min_weight.name: mx.quantization.quantize(args[conv_weight_name])[1],
             max_weight.name: mx.quantization.quantize(args[conv_weight_name])[2]}
    qconv_time = check_speed(sym=quantized_conv2d, location=qargs, ctx=ctx_gpu, N=repeats,
                             grad_req='null', typ='forward') * 1000

    print('==================================================================================================')
    print('data=%s, kernel=%s, num_filter=%s, pad=%s, stride=%s, no_bias=%s, layout=%s, repeats=%s'
          % (data_shape, kernel, num_filter, pad, stride, no_bias, layout, repeats))
    print('%s , ctx=%s, time=%.2f ms' % (conv_cudnn.name+'-FP32', ctx_gpu, conv_cudnn_time))
    print('%s, ctx=%s, time=%.2f ms' % (quantized_conv2d.name, ctx_gpu, qconv_time))
    print('quantization speedup:               %.1fX' % (conv_cudnn_time / qconv_time))
    print('\n')


if __name__ == '__main__':
    for batch_size in [32, 64, 128]:
        benchmark_convolution(data_shape=(batch_size, 64, 56, 56), kernel=(1, 1), num_filter=256,
                              pad=(0, 0), stride=(1, 1), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 56, 56, 64), kernel=(1, 1), num_filter=256,
                              pad=(0, 0), stride=(1, 1), layout='NHWC', repeats=20)

        benchmark_convolution(data_shape=(batch_size, 256, 56, 56), kernel=(1, 1), num_filter=64,
                              pad=(0, 0), stride=(1, 1), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 56, 56, 256), kernel=(1, 1), num_filter=64,
                              pad=(0, 0), stride=(1, 1), layout='NHWC', repeats=20)

        benchmark_convolution(data_shape=(batch_size, 256, 56, 56), kernel=(1, 1), num_filter=128,
                              pad=(0, 0), stride=(2, 2), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 56, 56, 256), kernel=(1, 1), num_filter=128,
                              pad=(0, 0), stride=(2, 2), layout='NHWC', repeats=20)

        benchmark_convolution(data_shape=(batch_size, 128, 28, 28), kernel=(3, 3), num_filter=128,
                              pad=(1, 1), stride=(1, 1), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 28, 28, 128), kernel=(3, 3), num_filter=128,
                              pad=(1, 1), stride=(1, 1), layout='NHWC', repeats=20)

        benchmark_convolution(data_shape=(batch_size, 1024, 14, 14), kernel=(1, 1), num_filter=256,
                              pad=(0, 0), stride=(1, 1), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 14, 14, 1024), kernel=(1, 1), num_filter=256,
                              pad=(0, 0), stride=(1, 1), layout='NHWC', repeats=20)

        benchmark_convolution(data_shape=(batch_size, 2048, 7, 7), kernel=(1, 1), num_filter=512,
                              pad=(0, 0), stride=(1, 1), layout='NCHW', repeats=20)
        benchmark_convolution(data_shape=(batch_size, 7, 7, 2048), kernel=(1, 1), num_filter=512,
                              pad=(0, 0), stride=(1, 1), layout='NHWC', repeats=20)
