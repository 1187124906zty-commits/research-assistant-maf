# Optional source-backed paragraph and figure exemplars

Six purpose-selected papers, five journals; an editorial starter set, not a representative journal corpus. The original paragraph contexts and figures were inspected in the source-learning task. Analyses are authored paraphrases. Every adaptation paragraph is explicitly hypothetical and supplies no empirical finding for another study. Read only a card whose reader decision fits the current task; inspect the original context before attributing a source convention.

<a id="ctx-001"></a>

## CTX-001: turn an unresolved scope question into a study response

Source: [10.1038/nphys3424](https://doi.org/10.1038/nphys3424), PDF p.1, actual Introduction / closing. Recommended adaptation target: introduction.

Authored context analysis: Established observations introduce two compaction regimes. The remaining uncertainty concerns conditions and mechanisms, rather than an absence of previous work. The closing unit presents experiments, a simple model and a regime map as complementary answers.

**Illustrative adaptation, not a quotation or reported result.** Existing measurements establish that cracks follow several distinct paths, but do not identify the conditions separating them. Here, we combine controlled loading tests with a discrete fracture model to examine how confinement changes crack localization. We use the resulting comparisons to map the transition between diffuse damage and a dominant crack.

Figure context (PDF p.2 Fig.2; p.3 Figs.3–4): Does the model reproduce observed patterns, and which variables organize their transitions? Experiment/model pairs across velocities, followed by breakage fields and a dimensionless regime map. The argument moves from observed patterns to a model diagnostic and then a regime interpretation.

Evidence care: Experimental and simulated velocities differ. Normalized resemblance is not a matched dimensional prediction; cereal and snow panels use different quantities.

Transfer: Use this closing move when the preceding paragraphs establish the question. Do not inherit the paper’s generality claim, spring model or phase groups. For exact model validation, show matched conditions and quantitative errors separately.

<a id="ctx-002"></a>

## CTX-002: connect unavailable measurements to a method choice

Source: [10.1038/s41524-022-00752-4](https://doi.org/10.1038/s41524-022-00752-4), PDF p.2, actual Introduction / closing. Recommended adaptation target: introduction.

Authored context analysis: The prior paragraph explains why path-dependent stress-label coverage becomes impractical. The response identifies what data are required and how physical constraints replace stress labels. The objective and representational choices become specific after the general response is recognizable.

**Illustrative adaptation, not a quotation or reported result.** Direct stress measurements are difficult to obtain in heterogeneous specimens, whereas displacement fields and reaction forces can be measured during loading. We therefore identify the constitutive response from these observables by enforcing mechanical equilibrium. The formulation separates the choice of candidate laws from their selection, allowing the inferred response to be examined for both accuracy and interpretability.

Figure context (PDF p.6 Table 2; p.7 Fig.3; p.8 Fig.4): Does discovery recover model behavior under noise, and do accurate curves imply correct parameter recovery? True versus discovered yield surfaces across models/noise; tabulated hidden/discovered parameters; deformation-path examples. Text distinguishes exact discovery, approximate behavior, false features and model-library mismatch.

Evidence care: Virtual experiments are not physical validation. Similar surfaces can coexist with parameter error. Fig.3 relative-stress representation does not capture kinematic hardening; Fig.4 adds absolute-stress views.

Transfer: Name the observable before the technical method. A library limitation should motivate an informative next test, not be erased. Use therefore only when the proposed method actually answers the preceding measurement problem.

<a id="ctx-003"></a>

## CTX-003: introduce an implemented model and its functional parts

Source: [10.1038/s41467-023-40854-1](https://doi.org/10.1038/s41467-023-40854-1), PDF p.2, actual Results / Overview of the generative ML approach / opening. Recommended adaptation target: methods.

Authored context analysis: The Introduction explains why desired responses and manufactured responses differ. The method opening names the implemented pipeline before defining its modules. Each module is explained through its input and output, giving readers functional orientation before architecture detail.

**Illustrative adaptation, not a quotation or reported result.** We implemented a two-stage identification procedure to recover the transport parameters from concentration profiles. The first stage estimates an initial parameter set from the boundary response; the second refines that set against the spatial profiles. Both stages use the same transport equations, so their difference lies in the information supplied to the fit rather than in the physical model.

Figure context (PDF p.5 Fig.3 and adjacent Results text): Are prescribed mechanical responses realized in manufactured specimens? Eight target/measured curve comparisons with matching specimen photographs. Manufactured response and repeat variability follow the inverse-design description.

Evidence care: Displayed measured curve is best matching among ten curves, not their mean. The band represents sample distribution. Y-axis ranges differ; compare fit within each panel. Do not adopt the paper’s expansive abstract claims as a universal style rule.

Transfer: Use module decomposition only for a genuinely modular method. Specify the selection rule if representative or best examples are shown. Preserve input/output clarity without importing source network architecture.

<a id="ctx-004"></a>

## CTX-004: show why an unsuccessful iteration changes the next experiment

Source: [10.1038/s41467-023-42415-y](https://doi.org/10.1038/s41467-023-42415-y), PDF p.5, actual Results / interpretation. Recommended adaptation target: results.

Authored context analysis: The target specifies both strength and an admissible modulus range. An intermediate strength increase violates the modulus target. The next iteration incorporates that information and produces candidates satisfying the joint goal. A manufactured control comparison follows the search trajectory.

**Illustrative adaptation, not a quotation or reported result.** The first refinement reduced the prediction error near the boundary but increased it in the specimen interior. This tradeoff suggests that the boundary fit alone does not constrain the spatial response. We therefore retained the governing equations and added an interior profile to the calibration, then evaluated the revised parameters on a separate exposure condition.

Figure context (PDF p.5 Fig.3): Can strength improve while the required modulus range and manufacturability are retained? Target bands and iteration groups; references; design/microCT correspondence; ML/control curves; architecture/stress map. Search progress includes target violations before final physical comparison and explanatory fields.

Evidence care: Property improvement must be judged jointly with constraints. Colored ellipses are search groups, not automatically uncertainty intervals. Stress contours alone do not establish a causal mechanism.

Transfer: Do not hide a failed iteration or change the target retrospectively. Keep a new confirmation condition independent of candidate selection. A successful search is not a general guarantee of algorithm superiority.

<a id="ctx-005"></a>

## CTX-005: introduce coupled model scope before constituent equations

Source: [10.1016/j.cemconres.2022.106861](https://doi.org/10.1016/j.cemconres.2022.106861), PDF p.2, actual Modelling approach / opening. Recommended adaptation target: methods.

Authored context analysis: The Introduction links missing interactions to the intended predictive use. The model opening specifies spatial/temporal outputs and exposure/material scope. A diagram separates early material development from deterioration and identifies the coupled processes.

**Illustrative adaptation, not a quotation or reported result.** We developed a coupled transport–reaction model to predict concentration and phase changes during salt exposure. Transport updates the pore-solution composition, which supplies the reaction calculation; the resulting phase changes then update the available pore space. The following sections define these exchanges and the initial and boundary conditions used in the comparisons.

Figure context (PDF p.9 Fig.6; p.11 Fig.9): Does the model reproduce spatial profiles across exposure solutions, times and measured quantities? Exposure columns, phase rows and consistent time encodings; additional chloride profiles. Observed profiles are followed by chemical and pore-structure interpretations, not just repeated ordinate values.

Evidence care: The abstract states adjustment of the initial tortuosity factor. Inspect data roles before calling every experimental overlay independent validation. Portlandite/carbonate and chloride use different drying bases.

Transfer: Teach functional coupling, not this paper’s chemistry. Reuse category encoding across panels but preserve measurement bases. A multi-observable agreement claim requires actual data for each observable.

<a id="ctx-006"></a>

## CTX-006: derive a model choice from an accuracy–cost tension

Source: [10.1016/j.cma.2024.117279](https://doi.org/10.1016/j.cma.2024.117279), PDF p.2, actual Introduction / transition. Recommended adaptation target: introduction.

Authored context analysis: Analytical models offer speed but struggle with complex microstructures. Direct simulation improves representation at higher cost. Reduced models address cost but raise data-support and extrapolation questions. The proposed architecture is introduced as a specific response to these tensions.

**Illustrative adaptation, not a quotation or reported result.** Direct simulations resolve the effect of microstructure on transport, but their cost limits repeated parameter studies. Reduced models make these studies more affordable, provided that the retained representation preserves the response of interest. We develop a reduced formulation around that response and assess its accuracy, computational cost and sensitivity to the training conditions.

Figure context (PDF p.9 Results description; p.10 Figs.6–7): Which model complexity is useful, and how stable is the training outcome? Training histories across geometries, error distribution, and parameter-set ablations across depths. The discussion distinguishes isotropic cases where extra parameters add little from orthotropic cases where rotations help.

Evidence care: Histories summarize 30 seeds; shaded region is described as a 95% confidence bound. The Fig.6d histogram uses one selected seed and offline-training points. Fig.7 compares training cost distributions, not independent generalization error.

Transfer: Separate optimization stability, approximation accuracy and generalization. Do not copy confidence-band semantics without its estimator. Use ablations only for interpretable changes and maintain fair budgets.
