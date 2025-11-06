// simple client-side validations for login/register forms
function validateLogin(form){
  const u = form.username.value.trim();
  const p = form.password.value.trim();
  if(!u || !p){
    alert('Enter username & password');
    return false;
  }
  return true;
}
