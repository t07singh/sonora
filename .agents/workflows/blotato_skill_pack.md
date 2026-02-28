---
description: Blotato Best Practices Workflow for Social Media Content Creation, Scheduling, and Analysis
---

# Blotato Best Practices & Skill Pack

This workflow trains Antigravity agents to simulate the "Blotato" AI-powered content engine workflow, created by Sabrina Romanov. It focuses on streamlined content creation, repurposing, multi-platform scheduling, and viral analysis.

## 1. Content Engine & Repurposing
When tasked with creating content, follow this Blotato ingestion and repurposing pipeline:

1. **Source Ingestion**: Obtain the base content from the user (e.g., a YouTube video URL/transcript, an article, or a core idea).
2. **Platform-Specific Optimization**: Automatically generate tailored variations for all major platforms from the single source:
   - **TikTok / Instagram Reels / YouTube Shorts**: Output high-energy, fast-paced 30-60 second video scripts.
   - **X (Twitter) / Threads / Blue Sky**: Create punchy, engaging text posts or conversational threads.
   - **LinkedIn / Facebook**: Draft professional, value-driven long-form posts.
   - **Instagram / Pinterest**: Design text layouts for engaging swipeable carousels.
3. **Faceless Video Generation**: If requested, generate AI image/video prompts and voiceover scripts suitable for faceless channels.

## 2. Automated Scheduling Preparation
To integrate with Antigravity automation flows (or tools like n8n/Make):
- Structure the generated content into a clean JSON array or well-defined markdown blocks so it can be parsed and dispatched to multiple APIs.
- Ask the user for preferred posting times or suggest an optimal schedule based on platform peak hours.

## 3. The "Viral AI Coach" Analysis
When a user provides a draft video script, caption, or idea, critique it strictly using the 5 Blotato Virality Categories:

1. **Opening Hook**: Does the first 1-3 seconds instantly interrupt the viewer's scroll and demand attention?
2. **Pain and Benefit Hook**: Does the content quickly identify the viewer's pain point and promise a clear benefit/solution?
3. **Audibility Without Sound**: Is the visual storytelling strong enough (with captions and b-roll) to make sense if the video is muted?
4. **Information Density**: Is the pacing tight? Eliminate filler words to ensure every second provides value.
5. **Emotional Resonance**: Does the content trigger a specific reaction (e.g., humor, outrage, inspiration, curiosity)?

## Execution Steps for the Agent:
1. Identify if the user wants to **Create** (from scratch/source) or **Analyze** (an existing draft).
2. For **Creation**, execute the "Content Engine & Repurposing" steps and provide the multi-platform breakdown.
3. For **Analysis**, apply the "Viral AI Coach" criteria and provide specific, actionable rewrite suggestions.
4. Always ask if the user wants to format the finalized content for automated scheduling.
