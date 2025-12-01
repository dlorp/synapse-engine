/**
 * ResponseDisplay Component Tests - Thinking Detection
 *
 * Validates the parseResponse() function's ability to detect and split
 * reasoning/thinking sections from model responses.
 *
 * Test Coverage:
 * - DeepSeek R1 format with <think> tags
 * - Qwen3-style reasoning patterns ("Okay, I need to...", "Let me think...")
 * - Conclusion marker detection ("In conclusion:", "Therefore:", etc.)
 * - Short responses that should NOT be split
 * - Edge cases (empty responses, thinking-only, etc.)
 */

import { describe, test, expect } from 'vitest';

/**
 * Extracted from ResponseDisplay.tsx for testing
 */
interface ParsedResponse {
  thinking: string | null;
  answer: string;
}

/**
 * Detect reasoning patterns commonly used in model thinking processes.
 */
function hasReasoningPatterns(text: string): boolean {
  const reasoningPatterns = [
    /\bLet me think\b/i,
    /\bI need to\b/i,
    /\bFirst,?\s/i,
    /\bSecond,?\s/i,
    /\bThird,?\s/i,
    /\bStep \d+:/i,
    /\bLet's break\b/i,
    /\bConsider\b/i,
    /\bAnalyzing\b/i,
    /\bExamining\b/i,
    /\bWe need to\b/i,
    /\bI should\b/i,
    /\bThis means\b/i,
    /\bTherefore,?\s/i,
  ];

  return reasoningPatterns.some(pattern => pattern.test(text));
}

/**
 * Parse response to detect reasoning/thinking sections from models like DeepSeek R1, Qwen3.
 * Separates verbose reasoning from the final answer.
 *
 * Detection strategies (in priority order):
 * 1. <think> tags - explicit thinking markers used by DeepSeek R1
 * 2. Reasoning pattern detection - "Let me think", "I need to", etc.
 * 3. Delimiter patterns - "Answer:", "In conclusion:", etc.
 * 4. Length heuristic with reasoning indicators
 */
function parseResponse(response: string): ParsedResponse {
  // PRIORITY 1: Check for <think> tags (DeepSeek R1 format)
  const thinkMatch = response.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch) {
    const thinking = thinkMatch[1].trim();
    const answer = response.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    if (thinking.length > 50 && answer.length > 0) {
      return { thinking, answer };
    }
  }

  // PRIORITY 2: Detect reasoning patterns at the START of response
  // This catches models like Qwen3 that start with "Okay, I need to..." or "Let me think..."
  const reasoningStartPatterns = [
    /^(Okay,?\s+(?:I need to|let me|so|first|let's))/i,
    /^(Let me (?:think|start|figure|analyze|consider))/i,
    /^(I need to (?:figure out|think about|consider|analyze))/i,
    /^(First,?\s+(?:I|let me|we))/i,
    /^(Hmm\.?\s+)/i,
    /^(Alright,?\s+(?:so|let me|I))/i,
    /^(So,?\s+(?:I need|let me|the user))/i,
    /^(To (?:answer|address|figure out|solve) this)/i,
  ];

  const startsWithReasoning = reasoningStartPatterns.some(pattern => pattern.test(response));

  // PRIORITY 3: Look for common answer delimiters
  const answerPatterns = [
    /(?:^|\n)(?:Final )?Answer:\s*/i,
    /(?:^|\n)In conclusion:?\s*/i,
    /(?:^|\n)Therefore:?\s*/i,
    /(?:^|\n)So,?\s+(?:in summary|to summarize|the answer)\b/i,
    /(?:^|\n)To summarize:?\s*/i,
    /(?:^|\n)Summary:\s*/i,
    /(?:^|\n)The answer is:?\s*/i,
    /(?:^|\n)In short:?\s*/i,
    /(?:^|\n)(?:Based on|Given) (?:this|the above|my analysis):?\s*/i,
  ];

  for (const pattern of answerPatterns) {
    const match = response.match(pattern);
    if (match && match.index !== undefined) {
      const splitIndex = match.index + match[0].length;
      const thinking = response.slice(0, match.index).trim();
      const answer = response.slice(splitIndex).trim();

      if (thinking.length > 100) {
        return { thinking, answer };
      }
    }
  }

  // PRIORITY 4: If response starts with reasoning and is long, split it
  if (startsWithReasoning && response.length > 300) {
    // Look for transition to answer in the latter half
    const searchStart = Math.floor(response.length * 0.4);
    const latterHalf = response.slice(searchStart);

    // Look for conclusion indicators
    const conclusionPatterns = [
      /\n\n(?:So |Therefore |Thus |In conclusion|Based on|Given this|The answer|To answer)/i,
      /\n\n(?:Current|Today's|The weather|The date|Here's|For |To summarize)/i,
      /\.\s*(?:So,? |Therefore,? |Thus,? |In summary,? )/i,
    ];

    for (const pattern of conclusionPatterns) {
      const match = latterHalf.match(pattern);
      if (match && match.index !== undefined) {
        const actualIndex = searchStart + match.index;
        const thinking = response.slice(0, actualIndex).trim();
        const answer = response.slice(actualIndex).trim();

        if (thinking.length > 100 && answer.length > 50) {
          return { thinking, answer };
        }
      }
    }

    // If no clear conclusion found, use paragraph-based split
    const lastParagraph = response.lastIndexOf('\n\n');
    if (lastParagraph > response.length * 0.3 && lastParagraph < response.length * 0.9) {
      return {
        thinking: response.slice(0, lastParagraph).trim(),
        answer: response.slice(lastParagraph).trim(),
      };
    }

    // Fallback: treat entire response as thinking with a generic answer note
    if (response.length > 500) {
      return {
        thinking: response,
        answer: "[Model provided reasoning but no clear final answer. See thinking process above.]",
      };
    }
  }

  // PRIORITY 5: Long responses with reasoning indicators - more aggressive split
  if (response.length > 400 && hasReasoningPatterns(response)) {
    // Split at paragraph boundaries in the second half
    const midpoint = Math.floor(response.length * 0.5);
    const searchText = response.slice(midpoint);
    const paragraphBreak = searchText.indexOf('\n\n');

    if (paragraphBreak > 0) {
      const splitPoint = midpoint + paragraphBreak;
      return {
        thinking: response.slice(0, splitPoint).trim(),
        answer: response.slice(splitPoint).trim(),
      };
    }
  }

  // Short responses or no reasoning detected - no split needed
  return { thinking: null, answer: response };
}

// ==================== TESTS ====================

describe('ResponseDisplay - <think> tag detection (DeepSeek R1)', () => {
  test('extracts thinking from <think> tags', () => {
    const response = `<think>
First, I need to analyze the question. This is a complex problem requiring careful consideration.
I should break it down into steps.
</think>

The answer is 42.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('analyze the question');
    expect(result.answer).toBe('The answer is 42.');
  });

  test('handles multiple <think> blocks (removes all)', () => {
    const response = `<think>First consideration that is long enough to meet the 50 character minimum requirement for thinking detection.</think>
Some text here.
<think>Second thought that is also sufficiently long to be detected as thinking content.</think>
Final answer here.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).not.toContain('<think>');
    expect(result.answer).toContain('Some text here');
    expect(result.answer).toContain('Final answer here');
  });

  test('requires minimum thinking length (>50 chars)', () => {
    const response = `<think>Short</think>
Answer here.`;

    const result = parseResponse(response);
    // Too short, should not split
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });

  test('case-insensitive <think> tag matching', () => {
    const response = `<THINK>
This is reasoning in uppercase tags which should still be detected properly by the parser.
</THINK>

This is the final answer.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('reasoning in uppercase');
    expect(result.answer).toBe('This is the final answer.');
  });
});

describe('ResponseDisplay - Qwen3-style reasoning patterns', () => {
  test('detects "Okay, I need to..." pattern', () => {
    const response = `Okay, I need to figure out how to solve this problem. Let me break it down step by step.

First, I'll analyze the requirements. Then I'll consider the constraints.

In conclusion: The best approach is to use a binary search algorithm.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('break it down step by step');
    expect(result.answer).toContain('The best approach');
  });

  test('detects "Let me think..." pattern', () => {
    const response = `Let me think about this carefully. The user is asking about Python metaclasses.

I should explain what metaclasses are, how they work, and provide examples.

Therefore: A metaclass is a class of a class that defines how a class behaves.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('think about this carefully');
    expect(result.answer).toContain('A metaclass is');
  });

  test('detects "I need to figure out..." pattern', () => {
    const response = `I need to figure out the best way to explain this concept to the user.

Let me start by considering what they already know and build from there.

So, to summarize: The answer is that you should use async/await for asynchronous operations in Python.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('use async/await');
  });

  test('detects "First," pattern at start', () => {
    const response = `First, let me understand what the user is asking. They want to know about Docker networking.

I'll explain the different network modes and their use cases.

The answer is: Docker supports bridge, host, overlay, and macvlan network modes.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('Docker supports');
  });

  test('detects "Hmm." pattern', () => {
    const response = `Hmm. This is an interesting question about quantum mechanics. I need to be precise here.

Let me explain the concept of superposition first, then discuss entanglement.

Based on this: Quantum states can exist in multiple states simultaneously until measured.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('Quantum states can');
  });
});

describe('ResponseDisplay - conclusion marker detection', () => {
  test('splits on "Answer:" delimiter', () => {
    const response = `This is a complex question requiring some analysis. Let me work through it step by step to understand all the implications.

Answer: The solution is to use a hash map with O(1) lookup time.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('complex question');
    expect(result.answer).toBe('The solution is to use a hash map with O(1) lookup time.');
  });

  test('splits on "In conclusion:" delimiter', () => {
    const response = `Let me analyze the pros and cons of each approach. First, consider performance. Second, consider maintainability. Third, consider scalability.

In conclusion: The best approach is option B due to better scalability.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('option B');
  });

  test('splits on "Therefore:" delimiter', () => {
    const response = `Based on the evidence presented and the analysis of all factors involved, we can draw some important conclusions here.

Therefore: The hypothesis is correct and the experiment validates our theory.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('hypothesis is correct');
  });

  test('splits on "To summarize:" delimiter', () => {
    const response = `There are multiple factors to consider when evaluating this question. Performance is critical. Security is important. Cost matters too.

To summarize: Choose the solution that balances all three factors effectively.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('balances all three factors');
  });

  test('splits on "The answer is:" delimiter', () => {
    const response = `This requires careful consideration of several variables and their interactions. We must analyze each factor thoroughly to understand the complete picture. The complexity of the problem demands a systematic approach.

The answer is: 42 is indeed the answer to life, the universe, and everything.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('42 is indeed');
  });

  test('requires minimum thinking length for delimiter split (>100 chars)', () => {
    const response = `Short intro.

Answer: The answer.`;

    const result = parseResponse(response);
    // Thinking section too short (<100 chars)
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });
});

describe('ResponseDisplay - paragraph-based splitting', () => {
  test('splits long reasoning response with paragraph break', () => {
    const response = `Okay, I need to analyze this problem carefully. First, let me consider the requirements and constraints. The user wants a solution that is both efficient and maintainable.

I should evaluate several approaches:
1. Option A has good performance but poor maintainability
2. Option B balances both concerns
3. Option C is highly maintainable but slower

Based on all of these factors, the optimal solution is Option B which provides the best balance between performance and code maintainability.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('analyze this problem');
    expect(result.answer).toContain('optimal solution is Option B');
  });

  test('uses paragraph-based split for long reasoning without clear delimiter', () => {
    const response = `Let me work through this step by step to understand the problem fully and ensure we cover all important aspects.

Step 1: Identify the core issue and understand its root causes
Step 2: Analyze possible solutions and their trade-offs carefully
Step 3: Evaluate trade-offs considering performance, maintainability, and scalability

The recommended approach is to use method X for this use case because it provides the best balance.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('recommended approach');
  });

  test('fallback to generic answer for very long reasoning without clear conclusion', () => {
    // Create a long response (>500 chars) that starts with reasoning but has no clear conclusion
    const longReasoning = `Okay, I need to think about this carefully. ${'This is detailed analysis. '.repeat(50)}`;

    const result = parseResponse(longReasoning);
    expect(result.thinking).toBe(longReasoning);
    expect(result.answer).toContain('[Model provided reasoning but no clear final answer');
  });
});

describe('ResponseDisplay - short response handling', () => {
  test('does not split short direct answers', () => {
    const response = 'The capital of France is Paris.';

    const result = parseResponse(response);
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });

  test('does not split short responses with reasoning patterns if too short', () => {
    const response = 'Let me think. The answer is 42.';

    const result = parseResponse(response);
    // Too short to split (< 300 chars)
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });

  test('does not split moderate length response without reasoning patterns', () => {
    const response = `This is a straightforward answer without any reasoning patterns.
It's moderately long but doesn't trigger any of the detection heuristics because it lacks
the specific patterns we're looking for like "Let me think" or conclusion markers.`;

    const result = parseResponse(response);
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });
});

describe('ResponseDisplay - edge cases', () => {
  test('handles empty response', () => {
    const response = '';

    const result = parseResponse(response);
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe('');
  });

  test('handles whitespace-only response', () => {
    const response = '   \n\n   ';

    const result = parseResponse(response);
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });

  test('handles response with only <think> tags (no answer)', () => {
    const response = '<think>This is just thinking with no actual answer provided anywhere in the response.</think>';

    const result = parseResponse(response);
    // Requires answer.length > 0
    expect(result.thinking).toBeNull();
    expect(result.answer).toBe(response);
  });

  test('preserves newlines and formatting in answer', () => {
    const response = `<think>Some thinking here that will be separated from the answer below.</think>

The answer is:
- Point 1
- Point 2
- Point 3`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('- Point 1');
    expect(result.answer).toContain('- Point 2');
    expect(result.answer).toContain('- Point 3');
  });

  test('handles very long response with reasoning patterns (>400 chars)', () => {
    const response = `This is a response with reasoning patterns like "I need to consider" the following factors.
${'Additional reasoning content that makes this response longer than 400 characters. '.repeat(10)}

Final paragraph with the actual answer after all that reasoning.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('Final paragraph');
  });

  test('does not split if thinking would be too short (<100 chars) for delimiter', () => {
    const response = `Brief intro.

Answer: Detailed answer here.`;

    const result = parseResponse(response);
    expect(result.thinking).toBeNull();
  });

  test('uses paragraph-based split even if answer is short when response starts with reasoning', () => {
    const response = `Okay, I need to think about this carefully. Let me analyze the situation from multiple angles and consider all the relevant factors that might affect the outcome. This requires deep thought and thorough consideration of every aspect. I must ensure that I understand all implications before providing my final answer.

So, yes, that is my final answer after all this careful consideration.`;

    const result = parseResponse(response);
    // Starts with reasoning pattern ("Okay, I need to") and is >300 chars
    // Falls through to paragraph-based split
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('So, yes');
  });
});

describe('ResponseDisplay - hasReasoningPatterns helper', () => {
  test('detects "Let me think"', () => {
    expect(hasReasoningPatterns('Let me think about this.')).toBe(true);
  });

  test('detects "I need to"', () => {
    expect(hasReasoningPatterns('I need to analyze this carefully.')).toBe(true);
  });

  test('detects "First,"', () => {
    expect(hasReasoningPatterns('First, we should consider the options.')).toBe(true);
  });

  test('detects "Step N:"', () => {
    expect(hasReasoningPatterns('Step 1: Identify the problem.')).toBe(true);
    expect(hasReasoningPatterns('Step 42: Solve everything.')).toBe(true);
  });

  test('detects "Therefore,"', () => {
    expect(hasReasoningPatterns('Therefore, the answer is X.')).toBe(true);
  });

  test('case-insensitive pattern matching', () => {
    expect(hasReasoningPatterns('LET ME THINK')).toBe(true);
    expect(hasReasoningPatterns('let me think')).toBe(true);
  });

  test('returns false for text without reasoning patterns', () => {
    expect(hasReasoningPatterns('This is a simple answer.')).toBe(false);
    expect(hasReasoningPatterns('The capital of France is Paris.')).toBe(false);
  });
});

describe('ResponseDisplay - real-world scenarios', () => {
  test('handles DeepSeek R1 weather query', () => {
    const response = `<think>
Okay, I need to determine what the weather is like today. But wait, I don't have access to real-time data or the user's location.
The user didn't specify where they are. I should explain that I can't provide current weather information.
</think>

I don't have access to real-time weather data or your location. To get current weather information,
please check a weather service like weather.com or use your device's weather app.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain("don't have access to real-time data");
    expect(result.answer).toContain("I don't have access to real-time weather data");
  });

  test('handles Qwen3 coding question', () => {
    const response = `Okay, let me analyze this Python question. The user wants to know about list comprehensions.

I need to explain:
1. What list comprehensions are
2. The syntax
3. Provide examples
4. Compare to traditional loops

Therefore: List comprehensions provide a concise way to create lists. The syntax is [expression for item in iterable if condition].
For example: squares = [x**2 for x in range(10)].`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.thinking).toContain('analyze this Python question');
    expect(result.answer).toContain('List comprehensions provide a concise way');
  });

  test('handles complex multi-paragraph technical explanation', () => {
    const response = `Let me think about how to explain Docker networking clearly.

First, I should cover the basic network types. Then explain use cases for each.
Finally, provide examples of when to use which type.

In conclusion: Docker supports four main network modes:
1. Bridge - Default, isolated network for containers
2. Host - Container shares host's network stack
3. Overlay - Multi-host networking for Swarm
4. Macvlan - Assigns MAC address to container

Choose based on your isolation and performance requirements.`;

    const result = parseResponse(response);
    expect(result.thinking).not.toBeNull();
    expect(result.answer).toContain('Docker supports four main network modes');
  });
});
