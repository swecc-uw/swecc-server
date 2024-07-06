import { useState, useEffect } from 'react';
import api from '../api';

const ProfileView = ({ profile }) => {
  if (!profile) return <div>No profile found</div>;

  return (
    <div>
      <h1>Profile</h1>
      <p><strong>Name:</strong> {profile.first_name} {profile.last_name}</p>
      <p><strong>Email:</strong> {profile.email}</p>
      <p><strong>Role:</strong> {profile.role}</p>
      <p><strong>Major:</strong> {profile.major}</p>
      <p><strong>Graduation Date:</strong> {profile.grad_date}</p>
      <p><strong>Discord Username:</strong> {profile.discord_username}</p>
      <p><strong>Discord ID:</strong>{profile.discord_id}</p>
      <p><strong>LinkedIn:</strong> {profile.linkedin?.username}</p>
      <p><strong>GitHub:</strong> {profile.github?.username}</p>
      <p><strong>LeetCode:</strong> {profile.leetcode?.username}</p>
      <p><strong>Resume URL:</strong> <a href={profile.resume_url}>{profile.resume_url}</a></p>
      <p><strong>Location:</strong> {profile.local}</p>
      <p><strong>Bio:</strong> {profile.bio}</p>
    </div>
  );
}

const ProfileForm = ({ profile, setProfile, isCreating }) => {
  const [formData, setFormData] = useState({
    first_name: profile?.first_name || '',
    last_name: profile?.last_name || '',
    email: profile?.email || '',
    role: profile?.role || '',
    major: profile?.major || '',
    grad_date: profile?.grad_date || '',
    discord_username: profile?.discord_username || '',
    discord_id: profile?.discord_id || '',
    linkedin: { username: profile?.linkedin?.username || '', isPrivate: profile?.linkedin?.isPrivate || false },
    github: { username: profile?.github?.username || '', isPrivate: profile?.github?.isPrivate || false },
    leetcode: { username: profile?.leetcode?.username || '', isPrivate: profile?.leetcode?.isPrivate || false },
    resume_url: profile?.resume_url || '',
    local: profile?.local || '',
    bio: profile?.bio || '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('.')) {
      const [field, subfield] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [field]: { ...prev[field], [subfield]: value }
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    const method = isCreating ? 'post' : 'put';
    api[method]('/api/members/profile/', formData)
      .then(response => {
        if (response.status === 200 || response.status === 201) {
          alert(isCreating ? "Profile created successfully!" : "Profile updated successfully!");
          setProfile(response.data); // Update the profile state with the updated data
        } else {
          throw new Error("Unexpected response status");
        }
      })
      .catch(error => {
        console.error("Error saving profile:", error);
        alert("There was an error saving the profile.");
      });
  }

  return (
    <div>
      <h1>{isCreating ? "Create Profile" : "Update Profile"}</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>First Name</label>
          <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} />
        </div>
        <div>
          <label>Last Name</label>
          <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} />
        </div>
        <div>
          <label>Email</label>
          <input type="email" name="email" value={formData.email} onChange={handleChange} />
        </div>
        <div>
          <label>Role</label>
          <input type="text" name="role" value={formData.role} onChange={handleChange} />
        </div>
        <div>
          <label>Major</label>
          <input type="text" name="major" value={formData.major} onChange={handleChange} />
        </div>
        <div>
          <label>Graduation Date</label>
          <input type="date" name="grad_date" value={formData.grad_date} onChange={handleChange} />
        </div>
        <div>
          <label>Discord Username</label>
          <input type="text" name="discord_username" value={formData.discord_username} onChange={handleChange} />
        </div>
        <div>
          <label>Discord ID</label>
          <input type="text" name="discord_id" value={formData.discord_id} onChange={handleChange} />
        </div>
        <div>
          <label>LinkedIn Username</label>
          <input type="text" name="linkedin.username" value={formData.linkedin.username} onChange={handleChange} />
        </div>
        <div>
          <label>GitHub Username</label>
          <input type="text" name="github.username" value={formData.github.username} onChange={handleChange} />
        </div>
        <div>
          <label>LeetCode Username</label>
          <input type="text" name="leetcode.username" value={formData.leetcode.username} onChange={handleChange} />
        </div>
        <div>
          <label>Resume URL</label>
          <input type="text" name="resume_url" value={formData.resume_url} onChange={handleChange} />
        </div>
        <div>
          <label>Location</label>
          <input type="text" name="local" value={formData.local} onChange={handleChange} />
        </div>
        <div>
          <label>Bio</label>
          <textarea name="bio" value={formData.bio} onChange={handleChange} />
        </div>
        <button type="submit">{isCreating ? "Create Profile" : "Update Profile"}</button>
      </form>
    </div>
  );
}

const MemberPage = () => {
  const [view, setView] = useState("profile");
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get('/api/members/profile/')
      .then(response => {
        setProfile(response.data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Error fetching profile:", error);
        if (error.response && error.response.status === 404) {
          // Profile not found, but not an error
          console.log("Profile not found");
          setIsLoading(false);
        } else {
          console.error("Error fetching profile:", error);
          setIsLoading(false);
        }
      });
  }, []);

  if (isLoading) return <div>Loading...</div>;

  let content = null;
  switch (view) {
    case "profile":
      content = <ProfileView profile={profile} />;
      break;
    case "update":
      content = <ProfileForm profile={profile} setProfile={setProfile} isCreating={false} />;
      break;
    case "create":
      content = <ProfileForm profile={null} setProfile={setProfile} isCreating={true} />;
      break;
    default:
      content = <ProfileView profile={profile} />;
  }

  return (
    <div>
      <button onClick={() => setView("profile")}>View Profile</button>
      {profile ? (
        <button onClick={() => setView("update")}>Update Profile</button>
      ) : (
        <button onClick={() => setView("create")}>Create Profile</button>
      )}
      {content}
    </div>
  );
}

export default MemberPage;

