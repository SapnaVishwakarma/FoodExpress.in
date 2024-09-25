var menu = document.querySelector('#menu-bars');
var navbar = document.querySelector('.navbar');
var header=document.querySelector('.nav-header')
current = window.location.pathname;

if (current == '/') {
  console.log('Is the homepage.')
} else {
  header.style.position='static'
}
menu.onclick = () =>{
  if (header.style.position != 'fixed'){
  menu.classList.toggle('fa-times');
  navbar.classList.toggle('active');
  header.style.position='fixed'
  }
  else{
    menu.classList.remove('fa-times');
    navbar.classList.remove('active');
    header.style.position='static'
  }
}

function replace(cart){
  remove=document.getElementById('a'+cart)
  remove.style.display='none'
  form=document.getElementById('q'+cart)
  form.style.display='inline'
}