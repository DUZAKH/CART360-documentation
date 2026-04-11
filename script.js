const sections = ['a', 'b', 'c', 'd'];
const slideIndexes = { a: 1, b: 1, c: 1, d: 1 };

function plusSlides(n, section) {
  showSlides(slideIndexes[section] += n, section);
}

function currentSlide(n, section) {
  showSlides(slideIndexes[section] = n, section);
}

function createDots(section) {
  const slides = document.getElementsByClassName('mySlides-' + section);
  const container = document.getElementById('dots-' + section);
  for (let i = 0; i < slides.length; i++) {
    const dot = document.createElement('span');
    dot.className = 'dot';
    dot.onclick = (function(i) {
      return function() { currentSlide(i + 1, section); };
    })(i);
    container.appendChild(dot);
  }
}

function showSlides(n, section) {
  const slides = document.getElementsByClassName('mySlides-' + section);
  const dots = document.querySelectorAll('#dots-' + section + ' .dot');

  if (n > slides.length) slideIndexes[section] = 1;
  if (n < 1) slideIndexes[section] = slides.length;

  for (let i = 0; i < slides.length; i++) {
    slides[i].style.display = 'none';
  }
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove('active');
  }

  slides[slideIndexes[section] - 1].style.display = 'block';
  if (dots[slideIndexes[section] - 1]) {
    dots[slideIndexes[section] - 1].classList.add('active');
  }

  const counter = slides[slideIndexes[section] - 1].querySelector('.numbertext');
  if (counter) {
    counter.innerText = slideIndexes[section] + ' / ' + slides.length;
  }
}

// Init all sections
sections.forEach(section => {
  createDots(section);
  showSlides(1, section);
});