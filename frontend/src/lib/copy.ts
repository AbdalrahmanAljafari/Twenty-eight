export const copy = {
  brand: "Twenty-eight",

  home: {
    title: "Virtual try-on",
    description: "Upload your face and body in one simple flow.",
    startFlow: "Start flow",
  },

  flow: {
    title: "Try-on flow",
    description: "Face first, then body.",
    steps: [
      { id: "face", label: "Face" },
      { id: "body", label: "Body" },
      { id: "complete", label: "Done" },
    ],
  },

  face: {
    uploadTitle: "Upload a clear frontal photo of your face.",
    cropTitle: "Crop your face",
    cropHint: "Zoom out to add white space around your face. Output is 512 × 512 px.",
    cropApply: "Apply crop",
    cropApplying: "Applying…",
    zoomLabel: "Zoom",
    processing: "Processing…",
    resultTitle: "Your portrait",
    next: "Next",
    back: "Back",
    upload: "Upload",
    regenerate: "Regenerate",
  },

  providers: {
    title: "Model providers",
    extraction: "Extraction",
    generation: "Generation",
    validation: "Validation",
  },

  faceTips: [
    "Frontal view",
    "No extreme lighting",
    "No hair covering the face",
    "Inside the outline",
    "No makeup",
    "Straight pose",
  ],

  body: {
    frontTitle: "Body front image",
    sideTitle: "Body side image",
    uploadedTitle: "User uploaded images",
    validateMessage: "System validate and checking",
    heightLabel: "Height",
    heightUnit: "cm",
    ageLabel: "Age",
    ageUnit: "Years",
    next: "Next",
    back: "Back",
    submit: "Next",
    submitting: "Submitting…",
  },

  bodyFrontTips: ["Full body", "Fitted clothes", "A pose"],
  bodySideTips: ["Same distance", "No tilt", "Open arms"],

  complete: {
    title: "Done",
    message: "Your face and body data are saved.",
    restart: "Start over",
    home: "Home",
  },

  preview: {
    title: "Preview",
    facePortrait: "Face portrait",
    faceSource: "Face source",
    front: "Front",
    side: "Side",
    empty: "Preview will appear here",
  },
} as const;
