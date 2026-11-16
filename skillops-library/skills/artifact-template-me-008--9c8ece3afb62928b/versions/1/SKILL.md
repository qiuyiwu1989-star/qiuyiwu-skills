---
name: artifact-template-me-008
description: "Create an image using the ME-008 米绿编辑线描 template and its retained reference file. Use when the user selects this template, names ME-008 米绿编辑线描, or explicitly invokes $artifact-template-me-008. 用淡米底、活力绿、卷发圆眼镜粗线人物生成八种页型的整页演示图，按文字量选择构图。"
---

# ME-008 米绿编辑线描

Create an image from this template. Keep the reference file unchanged.


## 内容优先的表达构思

先理解内容，再设计讲法，最后应用视觉风格。本节优先于本Skill中的示例布局、默认页型及页数建议；用户明确指定的布局仍应遵守。模板固定视觉语言，不固定故事结构与构图。

生成前先形成一份简短表达简报：听众是谁；希望其理解、感受或采取什么行动；核心主张是什么；必须保留的事实、证据、限制与情绪转折是什么。已有信息足够就直接判断，不机械追问；只有影响讲法的关键缺失才询问。

根据内容选择叙事逻辑：故事按处境、变化、选择与结果推进；观点用依据、例子与成立条件支撑；机制明确参与者、作用和反馈；方法展示任务、操作与关键判断；选择按同维度比较与适用条件展开；文化表达可从生活细节、器物或场景进入。以上是候选讲法，不是另一组强制模板，允许混合或另创。

只有存在实质不同的讲法且用户尚未指定时，提出两种简短方向，解释各自突出什么；普通单页可自主选择，不把每次创作变成审批流程。单页确定表达任务，整套安排进入、推进、转折与停顿，再决定页数、构图、字图比例和视觉节奏。

封面、观点、对比等页型是参考词汇，不是必须凑齐的目录。允许纯文字页、证据页、连续场景或用户内容所需的新页型。不要为了套三步骤而改写过程、为了闭环添加因果、为了风格强放人物或器物；不能用通用口号替代原始细节。插画须解释动作、关系、证据或情绪，否则删掉或改为留白。

验收先看内容：能否说清本页为何采用这个讲法、图像增加了什么理解；原始事实、限定、情绪和关系是否保留；是否因套版发生删减、伪造或过度概括。再检查视觉一致性、文字可读性与尺寸。跨页保持字体、配色、笔触与必要角色一致，布局随内容变化。


## Workflow

1. Read `artifact-template.json` and resolve its paths relative to this skill directory.
2. Invoke $imagegen with the retained PNG as a reference image and the user's requested content as the edit or generation brief.
3. Treat the user's prompt and available sources as the content input. Do not invent factual claims merely to fill the composition.
4. Preserve the reference's visual language unless the user explicitly requests a deviation.
5. Visually inspect the generated image for fidelity and defects, then return the final image.

## Fidelity

Preserve the reference image's composition, visual hierarchy, palette, typography, material treatment, lighting, and recurring brand elements.

User instructions control requested content and explicit deviations. The retained reference controls layout and formatting where the user has not requested a change.


## 八页型套系规则（优先于复刻单张布局）

Read [template contract](references/template.md) and [style guide](references/style-guide.md). Use [spec](references/spec.json) to select the page type, and inspect references/assets/<CODE>.jpg. The retained main PNG is a visual anchor, not a requirement to reuse its green ribbon, wording or exact composition for every page. User content selects the layout. Preserve palette, character identity and ink language; adapt density and light/dark rhythm to the page's purpose. Local source study images are not required.
