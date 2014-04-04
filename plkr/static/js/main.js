(function(undefined){
  var interval, timeout;

  try {
    if (!post_reload)
    {
      return;
    }
  } catch(e) {
    return;
  }

  function call_dajaxice() {
    var date = new Date().toISOString();
    Dajaxice.main.get_new_posts(callback, {"date":date});
  }

  function callback(data) {
    try {
      var postStart = document.getElementById("posts");
      var start = postStart.children[1];
      var newPost;
      var nPosts = data.length;
      
      if (nPosts != 0)
      {
          date = new Date().toISOString();
      }

      for (var i = 0; i < nPosts; ++i)
      {
         newPost = document.createElement("div");
         newPost.innerHTML = data[i];
         postStart.insertBefore(newPost, start);  
      }
    } catch(e) { ; }
  }

  function startInterval() { 
    clearInterval(interval);
    interval = setInterval(call_dajaxice, 10000);
  }

  function stopInterval() {
    clearInterval(interval);
  }

  function checkMouseActivity() {
    clearTimeout(timeout);
    timeout = setTimeout(stopInterval, 300000);
  }

  $(document).ready(function() {
    /* Assume activity when window is loaded */
    startInterval();

    /* Assume activity when window is active */
    $(window).focus(startInterval);

    /* Assume inactivity when window is not active */
    $(window).blur(stopInterval);

    /* Assume inactivity after 5 minutes of no mouse moves */
    $(window).mousemove(checkMouseActivity);
  });
})();