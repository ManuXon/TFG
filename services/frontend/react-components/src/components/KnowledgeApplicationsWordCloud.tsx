import React, { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";

const KnowledgeApplicationsWordCloud = ({ facultyName }: { facultyName: string }) => {
  const [imgUrl, setImgUrl] = useState<string | null>(null);
  const [gender, setGender] = useState("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);

  const fetchImage = useCallback(() => {
    const params = new URLSearchParams();
    if (gender && gender !== "All") params.append("gender", gender);
    if (experience) params.append("experience", experience);
    if (profile) params.append("profile", profile);

    const url = `http://localhost:8000/api/faculty/${facultyName}/knowledge-applications-wordcloud-image?${params.toString()}`;
    setImgUrl(url);
  }, [facultyName, gender, experience, profile]);

  useEffect(() => {
    fetchImage();
  }, [fetchImage]);

  return (
    <div className=""> {/* --- Filters Section --- */}
      <div className="flex flex-wrap justify-center gap-2 mb-6">
        <select value={gender} onChange={(e) => setGender(e.target.value)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" >
          <option value="All">All Genders</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Non-binary">Non-binary</option>
          <option value="No answer">No answer</option>
        </select>
        <select value={experience || ""} onChange={(e) => setExperience(e.target.value || null)}
                className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" >
          <option value="">All Experience</option>
          <option value="Less than 5">Less than 5</option>
          <option value="Between 5 and 10">Between 5 and 10</option>
          <option value="Between 11 and 20">Between 11 and 20</option>
          <option value="More than 20">More than 20</option>
        </select> <select value={profile || ""} onChange={(e) => setProfile(e.target.value || null)}
                          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" >
        <option value="">All Profiles</option>
        <option value="Senior Lecturer">Senior Lecturer</option>
        <option value="Associate">Associate</option>
        <option value="PreDoc">PreDoc</option>
        <option value="PostDoc">PostDoc</option>
        <option value="Collab">Collab</option>
        <option value="Lecturer">Lecturer</option>
        <option value="Professor">Professor</option>
      </select>
      </div>
      <h3 className="text-[22px] text-slate-800 mb-4 text-center"> Conceptual WordCloud of Familiarity with AI Functionalities </h3>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: imgUrl ? 1 : 0 }}
        transition={{ duration: 0.8 }}
        className="flex justify-center items-center w-full"
      >
        {imgUrl ? (
          <img
            src={imgUrl}
            alt="AI Word Cloud"
            className="rounded-lg shadow-sm border border-slate-200 max-w-full"
            style={{ maxHeight: "420px", objectFit: "contain" }}
          />
        ) : (
          <p className="text-gray-500">Loading word cloud...</p>
        )}
      </motion.div>
    </div>
  );
};

export default KnowledgeApplicationsWordCloud;
