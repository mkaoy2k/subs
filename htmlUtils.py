css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
'''

ver_template = '''
<div class="chat-message bot">
    <div class="message">{{MSG}}</div>
    <div class="avatar">
        <img src="https://github.com/mkaoy2k/Images/blob/main/mkao2019.jpeg?raw=true" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">
        <a href="https://github.com/mkaoy2k">Michael Kao</a><br />
        Creator, FamilyTrees<br />
        <a href="mailto:mkaoy2k@gmail.com">Contact me via Email</a><br />
    </div>
</div>
'''