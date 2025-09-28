const parallax_el = document.querySelectorAll('.parallax');

let xvalue = 0,yvalue = 0;
let rotationDeg = 0

window.addEventListener("mousemove",(e)=>{
    if (timeline.isActive()) return;
    xvalue = e.clientX - window.innerWidth/2;
    yvalue = e.clientY - window.innerHeight/2;
    rotationDeg = (xvalue/(window.innerWidth/2))*20

    parallax_el.forEach((el)=>{
        let speedZ = el.dataset.speedz;
        let speedX = el.dataset.speedx;
        let speedY = el.dataset.speedy;
        let speedR = el.dataset.rotate;

        let isLeft = parseFloat(getComputedStyle(el).left) < window.innerWidth/2 ? 1 :-1;
        let zvalue =(e.clientX - parseFloat(getComputedStyle(el).left))*isLeft *0.1;

        el.style.transform = `perspective(2300px) translateX(calc(-50% + ${-xvalue*speedX}px))  
        translateY(calc(-50% + ${yvalue*speedY }px)) 
          translateZ(${zvalue*speedZ}px) rotateY(${rotationDeg*speedR}deg)`
    })
})
// GSAP library 
let timeline  = gsap.timeline();
Array.from(parallax_el).filter((e)=> !e.classList.contains("text")).forEach((e)=>{
    gsap.from(
        e,
        {
            top:`${e.offsetHeight / 2 + +e.dataset.distance}px`,
            duration:3.5,
            ease: "power3.out",
        },
        "<" 
    );
});

timeline.from(".text h1",{
    y: window.innerHeight - document.querySelector(".text h1").getBoundingClientRect().top+200,
    duration:2,
},"1.5").from(".text h2",{
    y:-150,
    opacity:0,
    duration:1.5,
},"2")
.from(".hide",{
    opacity:0,
    duration:1.5,
},"2.1")