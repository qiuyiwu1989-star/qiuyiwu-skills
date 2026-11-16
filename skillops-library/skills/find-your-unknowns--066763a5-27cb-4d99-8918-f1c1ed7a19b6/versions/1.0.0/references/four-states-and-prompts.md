# 四状态与九动作：原文摘录

> 摘自 Thariq Shihipar《A field guide to Claude Fable 5: Finding your unknowns》
> Anthropic 官方，2026-07-06
> https://claude.com/resources/articles/a-field-guide-to-claude-fable-finding-your-unknowns

---

## 0. 核心比喻：地图 vs 疆域

> "The map, a representation of the work to be done, is my prompts and skills and context, it's what I give Claude. The territory is where the work needs to happen, the codebase, the real world, its actual constraints."
>
> **"The difference between the map and the territory is what I call unknowns. When Claude runs into an unknown, it needs to make a decision based on its best guess of what I want. The more work being done, the more unknowns Claude might run into."**

**关键判断**：
> "Claude Fable is the first model where I find **the quality of the work is bottlenecked by my ability to clarify its unknowns**."

**"只规划不够"**：
> "Importantly, **just planning ahead isn't always enough**. You can find unknowns deep in implementation, or **your unknowns may point you to the fact that you should actually be solving the problem in a different way altogether**."
>
> "I've found that working with Fable is an **iterative process of discovering my unknowns before, during, and after implementation**."

---

## 1. 四种状态（原文定义）

> "**Known Knowns**: This is essentially what is in my prompt. What do I tell the agent that I want?"
> "**Known Unknowns**: What haven't I figured out yet, but I'm aware that I haven't?"
> "**Unknown Knowns**: What's so obvious I'd never write it down, but **would recognize it if I saw it**?"
> "**Unknown Unknowns**: What haven't I considered at all? What knowledge am I not aware of? **Do I know how good something can be?**"

**关于"顶尖的人是怎样的"**：
> "The best agentic coders have relatively few unknowns... They are deeply in-sync with both the codebase and the model behaviors."
> "**But they also assume unknowns. In many ways, reducing and planning for your unknowns is the skill of agentic coding.**"

**关于"太具体 vs 太含糊"**：
> "If you are too specific, Claude will follow your instructions even when a pivot may be more appropriate. If you are too vague, Claude will often make choices and assumptions based on industry best practices that may not be a fit for your task."

**关于"给 AI 你的起点"**：
> "The most important part of this process is **to give Claude context about your starting point**. For example, tell it where you are in your thought process; disclose your experience with the problem and codebase; and let it work with you **like a thought partner**."

---

## 2. 动手前（Pre-implementation）

### Blind Spot Pass（盲点扫描）
> "When starting work, one of the most useful things you can do is **understand your blind spots**... you're likely to have a lot of unknown unknowns."
> "You may not know what questions to ask, what good looks like, what historical work has been done, or what potholes to avoid."
> "**I like to use the literal words 'blind spot pass' and 'unknown unknowns.'** Giving it context on who you are and what you know is usually important."

**原文 prompt**：
- "I'm working on adding a new auth provider but I know nothing about the auth modules in this codebase. **Can you do a blind spot pass** to help me figure out my relevant unknown unknowns and help me prompt you better."
- "I don't know what color grading is but I need to grade this video. **Can you teach me to understand my unknown unknowns about color grading**, so that I can prompt better?"

### Brainstorms and prototypes（头脑风暴与原型）
> "When I'm working in an area with a lot of **unknown knowns, involving criteria I only know to define when I see it**, I like to ask Claude to brainstorm and prototype with me."
> "**It's extremely valuable to identify and verbalize unknown knowns early during prototyping, because finding them out during implementation can be (relatively) expensive.**"

**原文 prompt**：
- "I want a dashboard for this data but **I have no visual taste** and don't know what's possible. **Make me an HTML page with 4 wildly different design directions so I can react to them.**"
- "Before wiring anything up, **make a single HTML file mocking the new editor toolbar with fake data**. I want to react to the layout before you touch the real app."
- "Here's my rough problem: users churn after onboarding. Search the codebase and **brainstorm 10 places we could intervene, from cheapest to most ambitious**. I'll tell you which ones resonate."

**关于"几乎每个会话都从探索开始"**：
> "I also start almost every coding session with an exploration or brainstorming phase. This helps me start with intent to define the project's scope... Brainstorming prevents me from setting too narrow or too wide a scope."

### Interviews（访谈）
> "Once I've done sufficient brainstorming, I likely still have unknowns. In this case, **I ask Claude to interview me** about any unknowns or ambiguities."

**原文 prompt（最重要的一句）**：
- "**Interview me one question at a time** about anything ambiguous, **prioritize questions where my answer would change the architecture**."

### References（参考）
> "Sometimes you can't describe what you want in detail... **the best approach is a reference**. While you can include diagrams, documentation or pictures, **the absolute best reference is source code**."
> "This provides Claude much richer detail around the markup and structure, compared to for example a screenshot."

**原文 prompt**：
- "This Rust crate in vendor/rate-limiter implements the exact backoff behavior I want. Read it and reimplement the same semantics in our TypeScript API client."

### Implementation Plans（实施计划）
> "The plan focuses on the parts that might be most likely to change such as data models, type interfaces, or UX flows. **This allows Claude to surface things I might actually need to alter.**"

**原文 prompt**：
- "Write an implementation plan in HTML, but **lead with the decisions I'm most likely to tweak with**: data model changes, new type interfaces, and anything user-facing. Bury the mechanical refactoring at the bottom, I trust you on that part."

---

## 3. 过程中（During implementation）

### Implementation notes（实施笔记）
> "no matter how much planning you do, **there are always unknown unknowns lurking**. The agent may find during its work that it needs to take a different tack due to an edge case it found in the code."

**原文 prompt**：
- "Keep an implementation-notes.md file. **If you hit an edge case that forces you to deviate from the plan, pick the conservative option, log it under 'Deviations', and keep going.**"

---

## 4. 完成后（Post implementation）

### Pitches and explainers（提案与解释）
> "Building pitch and explainer artifacts in the final document helps:
> - Accelerate understanding when **reviewers start with the same unknowns you did**
> - Accelerate approvals when **experts want to see you accounted for the unknowns and common failure points they would have anticipated**"

**原文 prompt**：
- "**Package the prototype, the spec, and the implementation notes into a single doc** I can drop in Slack to get buy-in. Lead with the demo GIF."

### Quizzes（测验）
> "Claude might have accomplished a lot more than I realized. Reading the code diffs can only give me a light understanding..."

**原文 prompt**：
- "I want to make sure I understand everything that's happened in this change. Give me a HTML report on the changes... and **a quiz at the bottom on the changes that I must pass**."

---

## 5. 压舱案例：Fable 发布视频

> "The launch video for Fable **was edited end-to-end using Claude Code**. This was a new domain for me and I'm by no means an expert."

他的做法（教科书式地用了本技能）：
1. **从"我确实知道的"开始**（知道 Claude 能用代码剪视频、转写，但不确定够不够准）
2. **问机制**："让 Claude 解释 **Whisper 是怎么工作的**，我能不能用 ffmpeg 准确切掉 um 和长停顿"
3. **做原型**："用 **Remotion** 和一份转写做**原型视频**，看行不行"
4. **发现未知**："视频看起来发灰，我知道那是调色（color grading）的结果，**但我其实不懂调色**。第一次想让 Claude 出几个变体来选，然后意识到——**我不知道调色的'好'长什么样**。所以改成**让 Claude 教我调色，来发现我的未知**。"

---

## 6. 收束（原文）

> "The better models get, the more you can achieve with the right approach. **When a long-horizon task comes back wrong, it's likely you need to spend more time defining your unknowns** or creating an implementation plan that allows for you and Claude to adapt through them."
>
> "**Every explainer, brainstorm, interview, prototype, and reference is a cheap way to find out what you didn't know before it gets expensive to fix.**"
>
> "So start your next project by **asking Claude to help you find your unknowns**."

（配套阅读：《the new rules of context engineering for Claude 5 generation models》）
