let slideIndex = 1;



// Sections
const imageDescriptions = [
`Research and moodboard stage`,

`Soft robotics and Spirobs`,

`Main ideation.`,

`Protoyping stage.`,

`Material selection.`,

`Building legs.`,

`Building body`,

`code/interaction system`,

`plans.`,

`X.`,

`y`,

`z`,

`hello`,

`more.`,

`text`,

`end`
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
    dot.onclick = function () {
      currentSlide(i + 1);
    };
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
  if (dots[slideIndex - 1]) {
    dots[slideIndex - 1].classList.add("active");
  }

  // 🔢 Update counter text dynamically
  let counter = slides[slideIndex - 1].querySelector(".numbertext");
  if (counter) {
    counter.innerText = slideIndex + " / " + slides.length;
  }

  // 🔥 Phrase change every 3 slides
  let phraseIndex = Math.floor((slideIndex - 1) / 3) % imageDescriptions.length;
  let textField = slides[slideIndex - 1].querySelector(".text");
  if (textField) {
    let phrase = imageDescriptions[phraseIndex];
textField.innerText = phrase;
textField.setAttribute("data-text", phrase);
  }

}


showSlides(slideIndex);