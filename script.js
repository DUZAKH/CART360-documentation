let slideIndex = 1;

// Descriptions for each slide
const imageDescriptions = [
  "Research and moodboard stage",
  "Soft robotics and Spirobs",
  "Main ideation.",
  "Prototyping stage.",
  "Material selection.",
  "Building legs.",
  "Code/interaction system",
  "Building body",
  "Plans.",
  "X.",
  "Y",
  "Z",
  "Hello",
  "More.",
  "Text",
  "End"
];

function plusSlides(n) {
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  showSlides(slideIndex = n);
}

// Create dots dynamically
function createDots() {
  let slides = document.getElementsByClassName("mySlides");
  let container = document.getElementById("dotsContainer");

  for (let i = 0; i < slides.length; i++) {
    let dot = document.createElement("span");
    dot.className = "dot";
    dot.onclick = function () { currentSlide(i + 1); };
    container.appendChild(dot);
  }
}

createDots();
showSlides(slideIndex);

function showSlides(n) {
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");

  if (n > slides.length) { slideIndex = 1; }
  if (n < 1) { slideIndex = slides.length; }

  for (let i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }

  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove("active");
  }

  slides[slideIndex - 1].style.display = "block";
  if (dots[slideIndex - 1]) dots[slideIndex - 1].classList.add("active");

  // Update text
  let textField = slides[slideIndex - 1].querySelector(".text");
  if (textField) {
    let phraseIndex = Math.floor((slideIndex - 1) % imageDescriptions.length);
    let phrase = imageDescriptions[phraseIndex];
    textField.innerText = phrase;
    textField.setAttribute("data-text", phrase);
  }

  // Update number
  let counter = slides[slideIndex - 1].querySelector(".numbertext");
  if (counter) counter.innerText = slideIndex + " / " + slides.length;
}
