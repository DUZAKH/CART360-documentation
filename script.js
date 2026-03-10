let slideIndex = 1;

// Descriptions for every 3 slides
const imageDescriptions = [
  "Research and moodboard stage",   // slides 1-3
  "Soft robotics and Spirobs",      // slides 4-6
  "Main ideation.",                 // slides 7-9
  "Prototyping stage",              // slides 10-12
  "Material selection",             // slides 13-15
  "Building legs",                  // slides 16-18
  "Building body",                  // slides 19-20
];

// Show next/previous slide
function plusSlides(n) {
  showSlides(slideIndex += n);
}

// Jump to specific slide
function currentSlide(n) {
  showSlides(slideIndex = n);
}

// Create navigation dots dynamically
function createDots() {
  const slides = document.getElementsByClassName("mySlides");
  const container = document.getElementById("dotsContainer");

  for (let i = 0; i < slides.length; i++) {
    const dot = document.createElement("span");
    dot.className = "dot";
    dot.onclick = function () { currentSlide(i + 1); };
    container.appendChild(dot);
  }
}

// Initialize dots
createDots();

// Display the initial slide
showSlides(slideIndex);

function showSlides(n) {
  const slides = document.getElementsByClassName("mySlides");
  const dots = document.getElementsByClassName("dot");

  if (n > slides.length) slideIndex = 1;
  if (n < 1) slideIndex = slides.length;

  // Hide all slides
  for (let i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }

  // Remove active state from dots
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove("active");
  }

  // Show current slide
  slides[slideIndex - 1].style.display = "block";

  // Highlight the current dot
  if (dots[slideIndex - 1]) {
    dots[slideIndex - 1].classList.add("active");
  }

  // Update number text
  const counter = slides[slideIndex - 1].querySelector(".numbertext");
  if (counter) {
    counter.innerText = slideIndex + " / " + slides.length;
  }

  // Update description text (every 3 slides share the same description)
  const textField = slides[slideIndex - 1].querySelector(".text");
  if (textField) {
    const phraseIndex = Math.floor((slideIndex - 1) / 3) % imageDescriptions.length;
    const phrase = imageDescriptions[phraseIndex];
    textField.innerText = phrase;
    textField.setAttribute("data-text", phrase);
  }
}