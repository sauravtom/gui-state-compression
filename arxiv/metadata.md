# arXiv Submission Metadata Draft

Title:
GUI State Compression for Computer-Use Agents Using Keyframes and Delta Encoding

Authors:
Saurav Tomar

Suggested primary category:
cs.AI

Suggested secondary categories:
cs.HC, cs.LG

Comments:
Workshop prototype. 10 pages, 4 figures. Code and benchmark artifacts available at https://github.com/sauravtom/gui-state-compression.

Abstract:
Computer-use agents commonly resend screenshots, DOM trees, accessibility trees, and accumulated history at every interaction step. This is wasteful because graphical user interfaces usually evolve incrementally: a form value changes, a modal appears, a page loads, or a table filter is applied. We frame GUI interaction as a compressible temporal signal and evaluate a keyframe-difference representation for agent context. The proposed hybrid method sends periodic screenshot keyframes plus semantic GUI deltas and compressed action history. In a deterministic 40-task custom browser benchmark, the hybrid method with keyframe interval K=4 reduces average input tokens from 6061.8 to 2877.2 per task, a 52.5% reduction, while preserving 90.0% success against a 100.0% full-context simulated baseline. This workshop prototype suggests that GUI state compression is a practical direction for reducing context cost and latency in computer-use agents, while also exposing failure modes around stale keyframes and imperfect semantic reconstruction.

Notes for final submission:
- Confirm the author name and affiliation before submitting.
- Confirm whether cs.AI is the desired primary category.
- arXiv requires an account and may require endorsement for new categories.
- Upload the generated source bundle from `dist/arxiv/gui-state-compression-arxiv.tar.gz`.
