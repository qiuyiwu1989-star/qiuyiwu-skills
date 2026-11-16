# 四个野心维度：完整原文摘录与展开

> 摘自 Felix Rieseberg《How to be more ambitious: A tutorial for humans with models》(2026-10-13)
> 英文原文：https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/

---

## 0. 为什么写这篇（作者自述）

- 他在 Claude 团队工作，每天看到别人用 Claude 做出他"没想到、以为不可能、或没时间试"的事。
- **模型能力不是均匀增长的**——Terry Tao 语："在某些方向惊人，在另一些方向不足。"
- **有些人驾驭了这些惊人能力、看上去在飞；更多人还在挣扎**，不知道除了"法国首都叫什么""帮我把这封邮件写得别那么冲"还能干嘛。
- 他自己承认："我们要更有野心"这种口号他喊了很多次，**但光喊没用**——所以这篇是把"野心"拆成可操作教程。

---

## 1. Speed（速度）——原文明确跳过

> "Speed: The same work in less time, the bread and butter for AI's economic value: If you need some code written, I'll do it faster with Claude. **Well established and requires little creativity in how you approach AI, so I'll skip this one.**"

**中文解读的补充**（什么值得买，2026-10-21）：2026 年还在为 AI 会员花钱的人，**会议纪要、周报、PPT、批量整理用户反馈大多已经跑顺**——"更快"对你**不是增量**。九篇解读口径各异，真正的新东西拧干后就三个动作：**往上抬目标、往下挖方法、往外借学科。**

---

## 2. Altitude（高度）

**原文定义**：
> "Going up in abstraction and considering the outcome rather than the individual task."

**核心追问**：
> "What do you want to happen next? What's the goal beyond the goal?"

**原文例子**：
> "At the beginning of last year, I still asked Claude to fix individual crashes for me. Eventually I asked Claude to simply **keep our apps crash-free**."

**QBR 四级阶梯（完整原文）**：
1. 最基础：填模板。
2. "Tell me what changed this quarter, why, and what we should do about it."（给它尽可能多的数据）
3. "Work out which three decisions are most urgent in the face of everything you've learned, and start working on potential directions with for/against arguments."
4. "The review exists so leadership catches problems early and moves money and people to the right places. **Design a better way to do that than a quarterly deck, show from our own history that it would have caught things sooner, and run it beside the current one for a quarter.**"

**适用性**：
- 最适合**你确实在追某个终极结果**时；**对创意类工作效果较差**。
- **好信号**：如果你本来就要开会讨论这件事，抬高度就是对的。
- **当前边界**："Claude, go make money" 在 2026 年对多数生意还不管用。
- **趋势判断**：模型能力越强，越能操作更高抽象层。

**关键代价（原文）**：
> "Altitude is also where people find **durable workflows that take the human out of the loop**... **Doing this well often involves changing your workflow** — in order to let Claude make sure our app is crash-free, I first had to make sure it can easily **fetch crash reports, understand which app version maps to what git commit, and give it access to Windows, macOS, and Linux computers** so it can actually independently reproduce and verify fixes."

---

## 3. Depth（深度）

**原文定义**：
> "Considering a task the way a field-leading expert would. Rather than operating at the task's layer, we go one level deeper and touch the underlying data, tools, and problems."

> "Being ambitious in depth means pushing the model to use the tools, techniques, media, and knowledge employed by **the best professionals in the field** — and to keep pushing **until even those people might learn something new from your work**."

**五招（原文）**：

1. **Insist on the same instruments used by the best in the industry**
   > "When prompted to act like a professional, models often **switch vocabulary without actually switching methods**... When Claude reaches for markdown tables, **insist on the use of databases and statistical models**. You don't necessarily have to know what the experts use, Claude usually does."

2. **Pick unreasonable goals and tell the model that they're very reasonable**
   > "You need your website to load in 5s instead of 10s? **Ask for 200ms.** Does something seem impossible to the model? Reiterate that it's very much solvable, it just needs to keep going."

3. **Challenge what you know**
   > "Especially in business, a lot of things we believe to be true are **rough approximations of reality**... 'We believe churn is an onboarding problem. **Try to reproduce that from the raw data.**'"

4. **Produce new knowledge**
   > "Build a simulation of our customers that reproduces the last year from our logs. Then **find the earliest signal of churn we don't know about yet, and show it predicts on data it has not seen**."

5. **Use an outside judge**
   > "**Do not ask the model to judge itself.** I assume that this will eventually be solved with increasing model intelligence, but **in October 2026, I implore you to insist on outside validation**. Ideally that's a tool the model can run to get feedback immediately."

**深度 prompt 模板（原文原样）**：
```
I want a deeper version of this task, not a bigger one. Before rewriting it:
(1) say what a top professional in this field would do here that I'm not asking for;
(2) name the rawest material they would start from instead of what has already been digested for me;
(3) name the specific methods and tools they would use;
(4) say what, other than you or me, would show the result is right.
Then rewrite my prompt to ask for exactly that.
```

---

## 4. Range（广度）

**原文定义**：
> "Drawing on multiple fields rather than just the one the task might need at the surface, using knowledge, tools, and techniques you normally wouldn't."

> "We consider our work from the perspective of different fields — **more fields than would have been economical in the past**. This isn't a particularly unique insight, **every single heist movie spends the first 30 minutes assembling a diverse cast of characters and talents**."

**作者自己的例子**：
> "Until I saw my colleague Alex Albert use Blender to render interior designs, **I never considered using Claude for 3D environments** for my homepage — even though I've previously made video games!"

**两招（原文）**：

1. **Try to replace the nouns with verbs**（出自 Tom Kelley & Jonathan Littman《The Art of Innovation》）
   > "A quarterly review isn't 'a deck'. It's '**getting busy people to believe a story about cause and effect, and to decide under uncertainty, in 30 minutes**'. Having the verbs makes it easier for **both me and Claude** to understand which fields might bring in a unique and useful perspective."

2. **Assemble the crew**
   > "The deck needs to be amazing, otherwise aliens will blow up Earth. What kind of team will humanity get together? For production quality, I'd bring in **an analyst, a journalist, and an editor**. If it has to be presented, probably **a motion and audio designer**, too. It might be useful to employ an adversarial 'red team', too, so let's bring in **a short seller and a forensic accountant**."
   >
   > **⚠️ "It is easy to accidentally engage in role play, which will make your transcript weirder without improving the actual outcome. Use this method to find fields and techniques. Don't ask the model to write like a short seller, ask it to do what a short seller does to research their position."**

**前提（原文）**：
> "All the ways in which I describe ambition require the model to have **a computer with the ability to install software and access to all kinds of relevant data** (either using MCP connectors or other means)."

---

## 5. 底层：自我效能感（Self-efficacy）

**原文**：
> "We humans have always been held back by **what we believe possible** — and what's worse, we usually trust ourselves only in very narrow disciplines. **Michelangelo famously didn't want to paint the Sistine Chapel — you see, he was a sculptor, not a painter.**"

> "Psychologists call this **self-efficacy**. People with high self-efficacy **believe in their own abilities more, and in turn actually accomplish more**."

**三招（原文，有据可查）**：
- **Believe it possible → accomplish it**：1939 年 George Dantzig 迟到，把 Berkeley 统计课黑板上**两道未解难题**当作业做了、交了。
- **Watch someone else do it → accomplish it**：四分钟一英里 Bannister 1954 年 5 月打破，**"唯一做到"仅保持 46 天**；两小时马拉松，Sawe 在伦敦跑出首个官方 sub-2，**同场比赛第二名也破了**。
- **Give yourself permission to fail**：《The Inner Game of Tennis》核心论点——**"如果你真的、非常努力地打，反而打不出最好的球"**；Linux 公布时号称"just a hobby, won't be big and professional like gnu"。

**收束（原文）**：
> "Self-efficacy isn't a new problem, but **it is a more powerful one now**. In a world where our abilities make leaps every couple of weeks, we need techniques that allow us to do things **we didn't really consider or believe possible**."

---

## 6. 全文结论

> "If you find more techniques that allow you to be more ambitious, please let me know!"

（配图：Francisco Goya《Modo de volar / A Way of Flying》——飞行方式的荒诞图，暗喻"人类想象飞行"的局限与突破。）
