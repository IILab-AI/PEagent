![start logo](images/start.png)
# PE Agent：Bridge the gap between AI and PE
## 1.框架简介
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您好，很高兴认识您！我是 PE Agent-谋略，PE Agent 家族里的第一个正式成员。 <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;电力电子（Power Electroncis, PE）领域的工作方式正面临着一场由人工智
能（Artificial Intelligence, AI）技术驱动的变革。在未来，我们必须以新的方式
去思考和实践，才能最大限度地发挥 AI 工具的潜力。但是，对于大部分电力电
子从业人员而言，AI 和 PE 之间仍存在一道鸿沟——想把 AI 用于 PE，但不知
道如何开始，急需一些科普知识和工具。 <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;于是，华中科技大学电气学院的陈宇教授团队和他的学生们（他们把自己
的团队称为"Impulse Intelligence Lab, 冲量智能实验室，简称 IIL"，把电力电子
的基础定理——冲量等效定理的前两个字，以及人工智能的后两个字，拼接在
一起，我认为很妙）企图跨越这道鸿沟，于是他们创造了我。我不知道他们是
否能成功，但我会努力完成他们交给我的任务。 <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;我是一个为电力电子量身定制的框架（或许也适用于更多领域）。据说我
的设计动机和理念源于陈宇教授对电力电子教学、科研和产品研发的一些切身
感悟，以及他对于 AI 的一些粗浅理解。他们发表了一篇关于我的论文，如果您
有兴趣，可以查阅： <br>
> 陈宇，祝之森，白敬波，商毅，康勇，“电力电子设计智能化：技术路线综述和前沿探索”，中国电机工程学报，DOI：10.13334/j.0258-8013.pcsee.241598（已录用，但也许还要过一段时间才能见刊）
>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;读完论文后，您会发现，我并不高端，仅仅是一种使用 AI 的理念，态度和
方式。我存在的意义和使命是： 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;（1）普及使用 AI 的更便捷之道，以及一些新的理念； <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;（2）帮助您快速构建出自己的"电力电子智能助手"； <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;（3）我有潜力作为电力电子设计的"大本营"，调用您编写的函数，甚至调
用您桌面的软件。 <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;对了，我的创造者还托我拜托您，如果您受到我的启发发表了论文，记得
引用上面的论文；他们也十分希望您把设计出来的各种"电力电子智能助手"分
享给大家，让更多电力电子人感受到 AI 的便利。 

## 2.PE Agent-M 基本操作  
PE Agent-M 以国产大型语言模型（Large Language Model）为基础，目前
支持三种国产 LLM：GLM、Kimi 和 Qwen。为了使用这些模型，您需要申请自
己的 API。以下是 GLM 的 API 申请步骤，Kimi 和 Qwen 的申请步骤类似： 
（1）访问 GLM 官方网站并注册账户。 
进入网址 https://open.bigmodel.cn/ ，页面如图 1 所述。 
