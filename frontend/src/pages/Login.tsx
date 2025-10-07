export default function Login(){
  return (
    <section>
      <h1>Connexion</h1>
      <form style={{display:"grid",gap:8, maxWidth:320}}>
        <input placeholder="Email" />
        <input placeholder="Mot de passe" type="password" />
        <button type="button">Se connecter</button>
      </form>
    </section>
  );
}
