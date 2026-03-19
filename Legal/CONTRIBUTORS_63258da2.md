列的显卡需要使用cuda11。

#### Q：想在Mac上部署，从哪里下载预测库呢？

**A**：Mac上的Paddle预测库可以从这里下载：[https://paddle-inference-lib.bj.bcebos.com/mac/2.0.0/cpu_avx_openblas/paddle_inference.tgz](https://paddle-inference-lib.bj.bcebos.com/mac/2.0.0/cpu_avx_openblas/paddle_inference.tgz)

#### Q：内网环境如何进行服务化部署呢？

**A**：仍然可以使用PaddleServing或者HubServing进行服务化部署，保证内网地址可以访问即可。

#### Q: 使用hub_serving部署，延时较高，可能的原因是什么呀？

**A**: 首先，测试的时候第一张图延时较高，可以多测试几张然后观察后几张图的速度；其次，如果是在cpu端部署serving端模型（如backbone为ResNet34），耗时较慢，建议在cpu端部署mobile（如backbone为MobileNetV3）模型。

#### Q: 在使用PaddleLite进行预测部署时，启动预测后卡死/手机死机？

**A**: 请检查模型转换时所用PaddleLite的版本，和预测库的版本是否对齐。即PaddleLite版本为2.8，则预测库版本也要为2.8。

#### Q: 预测时显存爆炸、内存泄漏问题？

**A**: 打开显存/内存优化开关`enable_memory_optim`可以解决该问题，相关代码已合入，[查看详情](https://github.com/PaddlePaddle/P