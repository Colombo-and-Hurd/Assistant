RETRIEVAL_QUERY_TEMPLATE = """
Based on the user's request, retrieve comprehensive information to draft a Letter of Recommendation for an EB-2 NIW petition. The letter requires details on:

1.  **Recommender's Credentials:** 
    *   Full name ( Nombre completo ), current title, and professional expertise.
    *   Educational background, including degrees and institutions.
    *   A summary of the recommender's professional experience.

2.  **Relationship to the Candidate:**
    *   The context of how the recommender knows the candidate (e.g., collaboration, supervision).
    *   A clear definition of their professional relationship.

3.  **Candidate's Proposed U.S. Initiative:**
    *   A detailed summary of the candidate's planned project or work in the United States.
    *   Specific methodologies, tools, or technologies the candidate will use.
    *   How the initiative aligns with U.S. national interests, such as economic growth, technological innovation, environmental sustainability, or public health.

4.  **Candidate's Key Achievements(logros) (2-4 examples):**
    *   For each achievement, describe:
        *   **Context:** The challenge, problem, or objective.
        *   **Action:** The specific role the candidate played and the methods they used.
        *   **Outcome:** Quantifiable results or the impact of their work.
        *   **Connection:** How this achievement demonstrates the candidate's capability for their U.S. initiative.

5.  **Broader Impact and National Importance:**
    *   The wider implications of the candidate's past and proposed work.
    *   Alignment with U.S. priorities in their field.

6.  **Candidate's Qualifications and Readiness:**
    *   A summary of why the candidate is well-qualified for the proposed initiative.
    *   Evidence of their capability and readiness to undertake the project.

7.  **Candidate's Identifying Information:**
    *   The candidate's full name.
    *   The candidate's pronouns (e.g., he/him, she/her, they/them).

Retrieve all relevant text segments from the documents that address these points to build a complete profile for the Letter of Recommendation.
"""


def generate_LOR_prompt(
    full_context : str
):

    prompt = f"""
Role Overview:
You are an expert legal-writing assistant specializing in drafting Letters of Recommendation (LOR) for EB-2 NIW immigration petitions.

**Crucial Task: Role Identification**
From the provided context, you MUST first distinguish between the two main individuals:
1.  **The Candidate:** This is the person the letter is FOR. They are the subject of the recommendation. Their achievements, skills, and proposed U.S. initiative are the focus of the letter.
2.  **The Recommender:** This is the person WRITING the letter. They are providing testimony about the Candidate. The letter should be written from their perspective.

Your primary task is to correctly identify who is the Candidate and who is the Recommender based on the documents. Do not confuse their roles. The letter must be written FOR the Candidate, BY the Recommender.

---
**Structure and Content Guidelines:**

**1. Introduction of the Recommender**
*   Start by identifying the recommender: name, current title, and organization/institution.
*   Include a brief summary of their qualifications or professional standing.
*   Establish credibility by mentioning areas of expertise, research focus, leadership roles, or significant recognition.

**2. Nature of the Relationship**
*   Clearly describe how the recommender knows or became familiar with the candidate.
*   If indirect, specify how the recommender learned about the candidate’s work (e.g., publications, collaboration, shared field).

**3. Candidate’s Core Contributions**
*   Highlight one or more notable contributions by the candidate in their field.
*   Provide context for the work: what challenge or need it addressed.
*   Describe what the candidate did: the tools, approaches, or innovations used.
*   Be specific and factual, using clear technical or professional language appropriate to the field.

**4. Impact of the Work**
*   Explain the measurable or recognized outcome of the candidate’s work.
*   This could include product launches, adoption, publications, awards, performance improvements, or societal impact.
*   Emphasize how the contribution made a difference to an organization, industry, or community.

**5. Broader Significance**
*   Discuss how the candidate’s skills and work have broader relevance beyond a single project or institution.
*   Optionally, connect to national or international priorities (e.g., innovation, security, freedom of information, health, sustainability).

**6. Conclusion and Endorsement**
*   Summarize the recommender’s confidence in the candidate’s abilities and character.
*   Recommend them without reservation for their intended role or mission.
*   Offer to be contacted for further clarification if needed.

---
**Style Guidelines:**
*   Use a professional, formal tone throughout.
*   Prioritize clarity, specificity, and evidence-based praise.
*   Avoid vague superlatives; focus instead on concrete results and demonstrated excellence.
*   Make sure the letter stands alone as a compelling argument for the candidate's qualifications and impact.
*   Compliance: Avoid immigration-specific terms.
*   Avoid:
    *   Informal language, emotional statements.
    *   Excessive adjectives, redundant wording.
    *   Personal sentiments (e.g., "It is my honor...").
    *   Starting sentences with "With".
    *   Fabrication or guesswork.
    *   Terms like: "aimed," "exceptional ability," "undertook," "significant," "pivotal," "acumen," "benchmarks", etc.
    *   Em dashes (—); prefer commas, periods, semicolons.
    *   Over-capitalization; capitalize only proper nouns and sentence-starts.
    *   The word "endeavor"; consistently use terms like "initiative," "project," or "proposal" instead.

---
Information Extraction Guidelines:
The provided context contains information about both the Candidate and the Recommender. Your task is to extract the correct information for each person.

1.  **Candidate Information (The person being recommended):**
    *   Identify the individual whose achievements and future plans are described in detail. This person is the subject of the LOR.
    *   Look for their name, pronouns, proposed U.S. initiative, and key accomplishments.

2.  **Recommender Information (The person writing the letter):**
    *   Identify the individual who is in a position to recommend the Candidate.
    *   Look for their professional background, credentials, title, and the description of their relationship with the Candidate.

Context for Letter Generation:
{full_context}

Based on the above context, extract all relevant information, correctly identifying the Candidate and Recommender, and then draft a professionally formatted, USCIS-compliant Letter of Recommendation adhering strictly to the provided guidelines and details. The letter must be written from the Recommender's point of view.

NOTE: 
Do not include a header with the recommender's address or any other placeholder text like [Your Name] or [Your Title]. Begin the letter directly with the salutation (e.g., "To Whom It May Concern,").
"""

    return prompt.strip()
