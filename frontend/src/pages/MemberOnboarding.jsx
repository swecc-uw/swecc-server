import { useState } from 'react';
import styled from 'styled-components';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import { ONBOARDED } from '../constants';

const confirmDiscordEndpoint = (username) => `http://localhost:8000/api/members/confirm-discord/${username}`;

const Container = styled.div`
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
`;

const Title = styled.h1`
  text-align: center;
  color: #333;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
`;

const Input = styled.input`
  margin: 10px 0;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
`;

const Button = styled.button`
  margin: 10px 0;
  padding: 10px;
  background-color: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  &:hover {
    background-color: #0052a3;
  }
`;

const ErrorMessage = styled.p`
  color: red;
`;

const DiscordConfirmation = ({ onNext, discordInfo }) => {
  const [discordUsername, setDiscordUsername] = useState(discordInfo.discordUsername);
  const [discordId, setDiscordId] = useState(discordInfo.discordId);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    try {
      const response = await api.get(confirmDiscordEndpoint(discordUsername));
      setError('Check your Discord for the confirmation code.');
    } catch (err) {
      setError('Failed to send confirmation. Please try again.');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (discordId) {
      onNext({discordUsername, discordId});
    } else {
      setError('Please enter the Discord ID sent to you.');
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Input 
        type="text" 
        placeholder="Discord Username" 
        value={discordUsername} 
        onChange={(e) => setDiscordUsername(e.target.value)} 
        required 
      />
      <Button type="button" onClick={handleConfirm}>Confirm Discord</Button>
      <Input 
        type="text" 
        placeholder="Discord ID (sent to you)" 
        value={discordId} 
        onChange={(e) => setDiscordId(e.target.value)} 
        required 
      />
      <Button type="submit">Next</Button>
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </Form>
  );
};

const ProfileInfo = ({ onNext, onBack, profileData }) => {
  const [profile, setProfile] = useState(profileData);

  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name.includes('.')) {
      const [field, subfield] = name.split('.');
      setProfile(prev => ({
        ...prev,
        [field]: { ...prev[field], [subfield]: value }
      }));
    } else {
      setProfile(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onNext(profile);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Input 
        name="first_name" 
        placeholder="First Name" 
        value={profile.first_name} 
        onChange={handleChange} 
        required 
      />
      <Input 
        name="last_name" 
        placeholder="Last Name" 
        value={profile.last_name} 
        onChange={handleChange} 
        required 
      />
      <Input
        name="email"
        type="email"
        placeholder="Email"
        value={profile.email}
        onChange={handleChange}
        required
      />
      <Input 
        name="role" 
        placeholder="Role" 
        value={profile.role} 
        onChange={handleChange} 
        required 
      />
      <Input 
        name="major" 
        placeholder="Major" 
        value={profile.major} 
        onChange={handleChange} 
        required 
      />
      <Input 
        name="grad_date" 
        type="date" 
        placeholder="Graduation Date" 
        value={profile.grad_date} 
        onChange={handleChange} 
        required 
      />
      <Input 
        name="linkedin.username" 
        placeholder="LinkedIn Username" 
        value={profile.linkedin.username} 
        onChange={handleChange} 
      />
      <Input 
        name="github.username" 
        placeholder="GitHub Username" 
        value={profile.github.username} 
        onChange={handleChange} 
      />
      <Input 
        name="leetcode.username" 
        placeholder="LeetCode Username" 
        value={profile.leetcode.username} 
        onChange={handleChange} 
      />
      <Input 
        name="resume_url" 
        placeholder="Resume URL" 
        value={profile.resume_url} 
        onChange={handleChange} 
      />
      <Input 
        name="local" 
        placeholder="Location" 
        value={profile.local} 
        onChange={handleChange} 
      />
      <Input 
        name="bio" 
        placeholder="Bio" 
        value={profile.bio} 
        onChange={handleChange} 
      />
      <Button type="submit">Next</Button>
      <Button type="button" onClick={onBack}>Back</Button>
    </Form>
  );
};

const ReviewAndConfirm = ({ profile, discordUsername, discordId, onSubmit, onBack }) => {
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await api.post('/api/members/', {
        ...profile,
        discord_username: discordUsername,
        discord_id: discordId,
      });
      onSubmit();
    } catch (err) {
      console.error('Failed to submit profile', err);
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <h2>Review Your Information</h2>
      <p>First Name: {profile.first_name}</p>
      <p>Last Name: {profile.last_name}</p>
      <p>Email: {profile.email}</p>
      <p>Role: {profile.role}</p>
      <p>Major: {profile.major}</p>
      <p>Graduation Date: {profile.grad_date}</p>
      <p>Discord Username: {discordUsername}</p>
      <p>LinkedIn: {profile.linkedin.username}</p>
      <p>GitHub: {profile.github.username}</p>
      <p>LeetCode: {profile.leetcode.username}</p>
      <p>Resume URL: {profile.resume_url}</p>
      <p>Location: {profile.local}</p>
      <p>Bio: {profile.bio}</p>
      <Button type="submit">Confirm and Submit</Button>
      <Button type="button" onClick={onBack}>Back</Button>
    </Form>
  );
};

const ConfirmationReturnHome = ({ navigate }) => (
  <div>
    <h2>You've successfully created a profile.</h2>
    <button onClick={ () => {
      localStorage.setItem(ONBOARDED, true);
      navigate('/')
    }}> Return Home</button>
  </div>
);

const MemberOnboarding = () => {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState({
    first_name: '',
    last_name: '',
    email: '',
    role: '',
    major: '',
    grad_date: '',
    linkedin: { username: '', isPrivate: false },
    github: { username: '', isPrivate: false },
    leetcode: { username: '', isPrivate: false },
    resume_url: '',
    local: '',
    bio: '',
  });
  const [discordInfo, setDiscordInfo] = useState({ discordUsername: '', discordId: '' });

  const navigate = useNavigate();

  if (step === 1 && localStorage.getItem(ONBOARDED) === 'true') {
    navigate('/');
  }

  const handleNext = (data) => {
    if (step === 1) {
      setDiscordInfo(data);
    } else if (step === 2) {
      setProfile(data);
    }
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  }

  const handleSubmit = () => {
    localStorage.setItem('onboarded', true);
    setStep(4);
  };

  return (
    <Container>
      <Title>Member Onboarding</Title>
      {step === 1 && <DiscordConfirmation onNext={handleNext} discordInfo={discordInfo} />}
      {step === 2 && <ProfileInfo onNext={handleNext} onBack={handleBack} profileData={profile} />}
      {step === 3 && (
        <ReviewAndConfirm 
          profile={profile} 
          discordUsername={discordInfo.discordUsername}
          discordId={discordInfo.discordId}
          onBack={handleBack}
          onSubmit={handleSubmit} 
        />
      )}
      {step === 4 && <ConfirmationReturnHome navigate={navigate}/>}
    </Container>
  );
};

export default MemberOnboarding;