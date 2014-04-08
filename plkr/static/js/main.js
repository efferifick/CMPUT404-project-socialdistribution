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
    Dajaxice.author.get_new_posts(callback, {date: date, author_id: post_reload_id});
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


(function(undefined){
  $(document).ready(function() {
    var $file = $("#newpost-file");
    var $form = $("#newpost");
    var $messages = $("#messages");
    var $tokens = $("input[name=csrfmiddlewaretoken]");
      

    // Validate the file
    $file.change(function(){
      var $this = $(this)
      var file = this.files[0];
      var name = file.name;
      var size = file.size;
      var type = file.type;
      
      if (type.indexOf("image/") !== 0) {
        $this.val('');
        $this.parent().addClass("has-error");
      }
    });

    $form.submit(function(){
      var $this = $(this);

      /* Taken from http://stackoverflow.com/a/8758614 */
      var formData = new FormData($this[0]);

      console.log(formData)
      
      $.ajax({
          url: $this.attr('action'),
          type: $this.attr('method'),
          
          beforeSend: function() {
            // Clear error messages
            $messages.html("");

            // Disable all controls in the form
            $("#newpost :input").attr("disabled", "disabled");
          },

          success: function(data, status, xhr) {
            var $posts = $("#posts")
            var post = data.post;

            // Insert the post first
            $posts.children("h2").after(post);
            
            // Clear the values of input fields
            $("#newpost input, #newpost textarea").val("");
          },

          error: function(xhr, status, error) {
            // Show the error
            $messages.prepend('<p class="bg-danger">' + xhr.responseJSON.message + '</p>');
          },

          complete: function(xhr) {
            var cookies = (document.cookie? document.cookie.split(";") : [])
            var token = null;

            // Search for the csrf token cookie
            for (i=0;i<cookies.length;++i) {
              if (cookies[i].trim().indexOf("csrftoken") === 0) {
                token = cookies[i].split("=")[1];
                break;
              }
            }
            
            // Enable all controls
            $("#newpost :input").attr("disabled", null)

            // Renew the csfrtoken
            $tokens.val(token);
          },

          // Form data
          data: formData,

          // Options to tell jQuery not to process data or worry about content-type.
          cache: false,
          contentType: false,
          processData: false
      });

      return false
    })
  });
})();